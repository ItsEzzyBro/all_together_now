# members/views.py
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from member_management.models import Member, Family, Vistor
from django.db.models import Q, Count, F, IntegerField, Case, When, Value
from django.db.models.functions import Now, ExtractYear, ExtractMonth, ExtractDay
from datetime import date, time, timedelta
from django.utils import timezone 
from ministry.models import Ministry, MembersAndMinistries
from attendance.models import Event, EventSchedule, Attendance
from member_management.forms import MemberForm, FamilyForm, VistorForm
from ministry.forms import MinistryForm
from django import forms
from django.http import JsonResponse, HttpResponseForbidden
from all_together_now.context_processors import get_user_accessible_ministries
import json  
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

# ---------- Public pages ----------
def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def contact(request):
    return render(request, "contact.html")

def connection_card(request):
    return render(request, "connection_card.html")

# ---------- Auth-required pages ----------
@login_required
def dashboard(request):
    return render(request, "dashboard.html")

@login_required
def visitors_view(request):
    return render(request, "visitors.html")

@login_required
def events_list(request):
    # Get ministries the user has access to for action permissions
    accessible_ministries = get_user_accessible_ministries(request.user)
    accessible_ministry_ids = list(accessible_ministries.values_list('id', flat=True))
    
    # All events are viewable, but all ministries show in filter
    events_qs = Event.objects.all().prefetch_related('schedules').order_by('event_name')

    # Search by name
    q = request.GET.get('q', '').strip()
    if q:
        events_qs = events_qs.filter(event_name__icontains=q)

    # Ministry filter
    selected_ministries = request.GET.getlist('ministry')
    if selected_ministries and 'all' not in selected_ministries:
        try:
            mids = [int(x) for x in selected_ministries]
        except ValueError:
            mids = []
        if mids:
            events_qs = events_qs.filter(ministry__in=mids)

    # Status filter (active/inactive)
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        events_qs = events_qs.filter(is_active=True)
    elif status_filter == 'inactive':
        events_qs = events_qs.filter(is_active=False)
    
    # Schedule type filters
    schedule_types = request.GET.getlist('schedule_type')
    if schedule_types:
        from django.db.models import Q
        schedule_filter = Q()
        if 'one-time' in schedule_types:
            schedule_filter |= Q(schedules__date__isnull=False)
        if 'recurring' in schedule_types:
            schedule_filter |= Q(schedules__weekday__isnull=False)
        if schedule_filter:
            events_qs = events_qs.filter(schedule_filter).distinct()
    
    # Weekday filter (for recurring events)
    selected_weekdays = request.GET.getlist('weekday')
    if selected_weekdays:
        try:
            weekday_ints = [int(x) for x in selected_weekdays]
            events_qs = events_qs.filter(schedules__weekday__in=weekday_ints).distinct()
        except ValueError:
            pass
    
    # Date range filter (for one-time events)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        events_qs = events_qs.filter(schedules__date__gte=date_from).distinct()
    if date_to:
        events_qs = events_qs.filter(schedules__date__lte=date_to).distinct()

    # Gather filter data
    ministries = Ministry.objects.all().order_by('ministry_name')
    
    # Process schedules for each event
    from collections import defaultdict
    events_with_schedules = []
    for event in events_qs:
        one_time_schedules = defaultdict(list)
        recurring_schedules = defaultdict(list)
        
        for schedule in event.schedules.all():
            time_str = schedule.open_time.strftime('%I:%M %p').lstrip('0')  # 12-hour format, remove leading zero
            if schedule.date:
                one_time_schedules[schedule.date].append(time_str)
            elif schedule.weekday is not None:
                weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weekday_name = weekday_names[schedule.weekday]
                recurring_schedules[weekday_name].append(time_str)
        
        # Sort times for each date/weekday
        for date_key in one_time_schedules:
            one_time_schedules[date_key].sort()
        for weekday_key in recurring_schedules:
            recurring_schedules[weekday_key].sort()
        
        event.one_time_schedules = sorted(one_time_schedules.items())
        event.recurring_schedules = [(k, recurring_schedules[k]) for k in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] if k in recurring_schedules]
        events_with_schedules.append(event)

    context = {
        'events': events_with_schedules,
        'query': q,
        'ministries': ministries,
        'selected_ministries': selected_ministries,
        'status_filter': status_filter,
        'schedule_types': schedule_types,
        'selected_weekdays': selected_weekdays,
        'date_from': date_from,
        'date_to': date_to,
        'accessible_ministry_ids': accessible_ministry_ids,
    }
    return render(request, 'events.html', context)

@login_required
def event_create(request):
    if request.method == 'POST':
        event_name = request.POST.get('event_name', '').strip()
        event_description = request.POST.get('event_description', '').strip()
        ministry_id = request.POST.get('ministry')
        is_active = request.POST.get('is_active') == 'on'
        
        if event_name:
            event = Event.objects.create(
                event_name=event_name,
                event_description=event_description,
                is_active=is_active
            )
            if ministry_id:
                ministry = Ministry.objects.get(pk=ministry_id)
                event.ministry = ministry
                event.save()
            
            # Process schedules
            from datetime import datetime, timedelta
            schedule_index = 0
            while f'schedule_type_{schedule_index}' in request.POST:
                schedule_type = request.POST.get(f'schedule_type_{schedule_index}')
                start_time_str = request.POST.get(f'schedule_start_time_{schedule_index}', '08:30')
                duration_minutes = int(request.POST.get(f'schedule_duration_{schedule_index}', 90))
                
                # Parse start time and calculate close time
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                start_dt = datetime.combine(datetime.today(), start_time)
                close_dt = start_dt + timedelta(minutes=duration_minutes)
                close_time = close_dt.time()
                
                if schedule_type == 'one-time':
                    schedule_date = request.POST.get(f'schedule_date_{schedule_index}')
                    if schedule_date:
                        EventSchedule.objects.create(
                            event=event,
                            date=schedule_date,
                            weekday=None,
                            open_time=start_time,
                            close_time=close_time
                        )
                elif schedule_type == 'recurring':
                    schedule_weekday = request.POST.get(f'schedule_weekday_{schedule_index}')
                    if schedule_weekday:
                        EventSchedule.objects.create(
                            event=event,
                            date=None,
                            weekday=int(schedule_weekday),
                            open_time=start_time,
                            close_time=close_time
                        )
                
                schedule_index += 1
            
            return redirect('events')
    
    # Get preselected ministry from URL parameter
    preselected_ministry = request.GET.get('ministry', '')
    # Only show ministries the user has access to
    ministries = get_user_accessible_ministries(request.user).order_by('ministry_name')
    return render(request, 'event_form.html', {
        'ministries': ministries,
        'action': 'Create',
        'preselected_ministry': preselected_ministry
    })

@login_required
def event_edit(request, pk):
    event = Event.objects.get(pk=pk)
    accessible_ministries = get_user_accessible_ministries(request.user)
    accessible_ministry_ids = list(accessible_ministries.values_list('id', flat=True))
    
    # Check if user has permission to edit this event (if it has a ministry)
    if event.ministry and event.ministry.id not in accessible_ministry_ids:
        return HttpResponseForbidden("You don't have permission to edit this event.")
    
    if request.method == 'POST':
        event.event_name = request.POST.get('event_name', '').strip()
        event.event_description = request.POST.get('event_description', '').strip()
        ministry_id = request.POST.get('ministry')
        event.is_active = request.POST.get('is_active') == 'on'
        
        if ministry_id:
            # Verify user has access to the selected ministry
            if int(ministry_id) not in accessible_ministry_ids:
                return HttpResponseForbidden("You don't have permission to assign this ministry.")
            event.ministry = Ministry.objects.get(pk=ministry_id)
        else:
            event.ministry = None
        event.save()
        
        # Delete existing schedules and recreate from form data
        EventSchedule.objects.filter(event=event).delete()
        
        # Process schedules
        from datetime import datetime, timedelta
        schedule_index = 0
        while f'schedule_type_{schedule_index}' in request.POST:
            schedule_type = request.POST.get(f'schedule_type_{schedule_index}')
            start_time_str = request.POST.get(f'schedule_start_time_{schedule_index}', '08:30')
            duration_minutes = int(request.POST.get(f'schedule_duration_{schedule_index}', 90))
            
            # Parse start time and calculate close time
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            start_dt = datetime.combine(datetime.today(), start_time)
            close_dt = start_dt + timedelta(minutes=duration_minutes)
            close_time = close_dt.time()
            
            if schedule_type == 'one-time':
                schedule_date = request.POST.get(f'schedule_date_{schedule_index}')
                if schedule_date:
                    EventSchedule.objects.create(
                        event=event,
                        date=schedule_date,
                        weekday=None,
                        open_time=start_time,
                        close_time=close_time
                    )
            elif schedule_type == 'recurring':
                schedule_weekday = request.POST.get(f'schedule_weekday_{schedule_index}')
                if schedule_weekday:
                    EventSchedule.objects.create(
                        event=event,
                        date=None,
                        weekday=int(schedule_weekday),
                        open_time=start_time,
                        close_time=close_time
                    )
            
            schedule_index += 1
        
        return redirect('events')
    
    # Only show ministries the user has access to
    ministries = accessible_ministries.order_by('ministry_name')
    existing_schedules = EventSchedule.objects.filter(event=event).order_by('id')
    return render(request, 'event_form.html', {
        'event': event,
        'ministries': ministries,
        'action': 'Edit',
        'existing_schedules': existing_schedules
    })

@login_required
def event_delete(request, pk):
    event = Event.objects.get(pk=pk)
    accessible_ministries = get_user_accessible_ministries(request.user)
    accessible_ministry_ids = list(accessible_ministries.values_list('id', flat=True))
    
    # Check if user has permission to delete this event (if it has a ministry)
    if event.ministry and event.ministry.id not in accessible_ministry_ids:
        return HttpResponseForbidden("You don't have permission to delete this event.")
    
    if request.method == 'POST':
        event.delete()
        return redirect('events')
    return render(request, 'event_confirm_delete.html', {'event': event})

@login_required
def analytics_view(request):
    today = timezone.now().date()
    last_30 = today - timedelta(days=30)

    # Member stats
    members_qs = Member.objects.all()
    total_members = members_qs.count()

    # Gender stats
    gender_counts = (
        members_qs
        .values("gender")
        .annotate(count=Count("id"))
        .order_by()
    )
    gender_stats = [
        {
            "label": gc["gender"] or "Unspecified",
            "count": gc["count"],
        }
        for gc in gender_counts
    ]
    gender_labels = [g["label"] for g in gender_stats]
    gender_values = [g["count"] for g in gender_stats]

    # Age stats - compute in Python using Member.age property
    age_0_12 = age_13_17 = age_18_29 = age_30_49 = age_50_plus = 0
    for m in members_qs:
        try:
            age = m.age if m.date_of_birth else None
        except Exception:
            age = None
        if age is None:
            continue
        if 0 <= age <= 12:
            age_0_12 += 1
        elif 13 <= age <= 17:
            age_13_17 += 1
        elif 18 <= age <= 29:
            age_18_29 += 1
        elif 30 <= age <= 49:
            age_30_49 += 1
        elif age >= 50:
            age_50_plus += 1

    age_buckets = {
        "0–12": age_0_12,
        "13–17": age_13_17,
        "18–29": age_18_29,
        "30–49": age_30_49,
        "50+": age_50_plus,
    }
    age_labels = list(age_buckets.keys())
    age_values = list(age_buckets.values())

    # Attendance (last 30 days) 
    attend_last_30 = Attendance.objects.filter(date__gte=last_30)

    total_checkins_30 = attend_last_30.count()
    unique_events_30 = attend_last_30.values("event").distinct().count()

    if unique_events_30:
        avg_attendance_30 = round(total_checkins_30 / unique_events_30)
    else:
        avg_attendance_30 = 0

    # Recent attendance by date (last 7 dates)
    recent_attendance = (
        attend_last_30
        .values("date")
        .annotate(count=Count("attendee"))  # attendee is FK to Member
        .order_by("date")[:7]
    )
    attendance_trend = [
        {
            "date": row["date"],
            "count": row["count"],
        }
        for row in recent_attendance
    ]
    attendance_labels = [row["date"].strftime("%Y-%m-%d") for row in attendance_trend]
    attendance_values = [row["count"] for row in attendance_trend]

    # Ministry stats 
    ministries_qs = Ministry.objects.all().order_by("ministry_name")

    ministries_data = []
    for m in ministries_qs:
        member_count = (
            MembersAndMinistries.objects
            .filter(ministry=m)
            .values("member")
            .distinct()
            .count()
        )
        ministries_data.append({
            "name": m.ministry_name,
            "member_count": member_count,
            "is_active": getattr(m, "is_active", True),
        })
    ministry_labels = [m["name"] for m in ministries_data]
    ministry_values = [m["member_count"] for m in ministries_data]

    context = {
        "summary": {
            "total_members": total_members,
            "total_checkins_30": total_checkins_30,
            "unique_events_30": unique_events_30,
            "avg_attendance_30": avg_attendance_30,
        },
        "attendance_trend": attendance_trend,
        "gender_stats": gender_stats,
        "age_buckets": age_buckets,
        "ministries": ministries_data,

        # Chart.js JSON data
        "attendance_labels_json": json.dumps(attendance_labels),
        "attendance_values_json": json.dumps(attendance_values),
        "gender_labels_json": json.dumps(gender_labels),
        "gender_values_json": json.dumps(gender_values),
        "age_labels_json": json.dumps(age_labels),
        "age_values_json": json.dumps(age_values),
        "ministry_labels_json": json.dumps(ministry_labels),
        "ministry_values_json": json.dumps(ministry_values),
    }
    return render(request, "analytics.html", context)



@login_required
def system_view(request):
    return render(request, "system.html")

@login_required
def profile(request):
    # You can create a dedicated template later; using dashboard for now
    return render(request, "dashboard.html")

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    
    # Add Bootstrap classes to form fields
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    
    return render(request, "change_password.html", {'form': form})


# ---------- Member CRUD (user-facing) ----------
@login_required
def members_list(request):
    # Get ministries the user has access to
    accessible_ministries = get_user_accessible_ministries(request.user)
    accessible_ministry_ids = list(accessible_ministries.values_list('id', flat=True))
    
    # Handle bulk actions
    if request.method == 'POST':
        action = request.POST.get('bulk_action')
        selected_ids = request.POST.getlist('member_ids')
        if selected_ids:
            members_qs = Member.objects.filter(id__in=selected_ids)
            if action == 'delete':
                members_qs.delete()
                # Keep UI state: redirect back with action param so JS can preselect if needed
                return redirect(reverse('members_view') + f'?bulk_action=delete')
            elif action == 'add_to_ministry':
                ministry_id = request.POST.get('ministry_id')
                # Only allow if user has access to this ministry
                if ministry_id and int(ministry_id) in accessible_ministry_ids:
                    ministry = Ministry.objects.get(pk=ministry_id)
                    for member in members_qs:
                        MembersAndMinistries.objects.get_or_create(member=member, ministry=ministry)
                # Redirect back keeping the selected ministry and action in the URL
                return redirect(reverse('members_view') + f'?bulk_action=add_to_ministry&ministry_id={ministry_id}')
            elif action == 'remove_from_ministry':
                ministry_id = request.POST.get('ministry_id')
                # Only allow if user has access to this ministry
                if ministry_id and int(ministry_id) in accessible_ministry_ids:
                    MembersAndMinistries.objects.filter(member__in=members_qs, ministry_id=ministry_id).delete()
                return redirect(reverse('members_view') + f'?bulk_action=remove_from_ministry&ministry_id={ministry_id}')
            elif action == 'add_to_family':
                family_id = request.POST.get('family_id')
                if family_id:
                    family = Family.objects.get(pk=family_id)
                    members_qs.update(family=family)
                return redirect(reverse('members_view') + f'?bulk_action=add_to_family&family_id={family_id}')
            elif action == 'remove_from_family':
                members_qs.update(family=None)
                return redirect(reverse('members_view') + f'?bulk_action=remove_from_family')

    # Queryset - filter to show only members from accessible ministries
    # Church Administrators see ALL members
    # Others see only members from ministries they have access to
    from member_management.models import UsersAndRoles, Role
    try:
        church_admin_role = Role.objects.get(role_name="Church Administrator")
        is_church_admin = UsersAndRoles.objects.filter(
            user=request.user, 
            role=church_admin_role
        ).exists()
    except Role.DoesNotExist:
        is_church_admin = False
    
    if is_church_admin:
        # Church Administrator sees ALL members
        qs = Member.objects.all().order_by('last_name', 'first_name')
    elif accessible_ministry_ids:
        # Other users see only members from their accessible ministries
        member_ids = MembersAndMinistries.objects.filter(
            ministry_id__in=accessible_ministry_ids
        ).values_list('member_id', flat=True).distinct()
        qs = Member.objects.filter(id__in=member_ids).order_by('last_name', 'first_name')
    else:
        # No accessible ministries
        qs = Member.objects.none()

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        )

    # Filters: ministry, gender, marital status, age ranges
    # Ministry filtering: 'ministry' GET params may contain 'all' or ministry pks
    selected_ministries = request.GET.getlist('ministry')
    if selected_ministries and 'all' not in selected_ministries:
        # convert to ints where possible
        try:
            mids = [int(x) for x in selected_ministries]
        except ValueError:
            mids = []
        if mids:
            member_ids = MembersAndMinistries.objects.filter(ministry__in=mids).values_list('member_id', flat=True)
            qs = qs.filter(id__in=member_ids)
    genders = request.GET.getlist('gender')
    if genders:
        qs = qs.filter(gender__in=genders)

    statuses = request.GET.getlist('status')
    if statuses:
        qs = qs.filter(marital_status__in=statuses)
    age_ranges = request.GET.getlist('age')

    # If age ranges selected, filter in Python (safe for modest dataset sizes).
    members_list = list(qs)
    if age_ranges:
        def in_ranges(member_age, ranges):
            if member_age is None:
                return False
            for r in ranges:
                if r == '0-17' and member_age <= 17:
                    return True
                if r == '18-25' and 18 <= member_age <= 25:
                    return True
                if r == '26-40' and 26 <= member_age <= 40:
                    return True
                if r == '41-60' and 41 <= member_age <= 60:
                    return True
                if r == '60+' and member_age >= 61:
                    return True
            return False

        members_list = [m for m in members_list if in_ranges(getattr(m, 'age', None), age_ranges)]

    # Only show accessible ministries in the filter
    ministries = accessible_ministries.order_by('ministry_name')
    families = Family.objects.all().order_by('family_name')

    context = {
        'members': members_list,
        'query': q,
        'selected_genders': genders,
        'selected_statuses': statuses,
        'selected_ages': age_ranges,
        'age_choices': ['0-17', '18-25', '26-40', '41-60', '60+'],
        'ministries': ministries,
        'selected_ministries': selected_ministries,
        'available_families': families,
        'accessible_ministry_ids': accessible_ministry_ids,
    }
    return render(request, 'members.html', context)


@login_required
def member_create(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            new_family_name = request.POST.get('new_family_name', '').strip()
            member = form.save(commit=False)
            if new_family_name:
                family, _ = Family.objects.get_or_create(family_name=new_family_name)
                member.family = family
            member.save()
            form.save_m2m()
            return redirect('members_view')
    else:
        form = MemberForm()
    return render(request, 'member_form.html', {'form': form, 'action': 'Create'})


@login_required
def member_edit(request, pk):
    member = Member.objects.get(pk=pk)
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            new_family_name = request.POST.get('new_family_name', '').strip()
            member_obj = form.save(commit=False)
            if new_family_name:
                family, _ = Family.objects.get_or_create(family_name=new_family_name)
                member_obj.family = family
            member_obj.save()
            form.save_m2m()
            return redirect('members_view')
    else:
        form = MemberForm(instance=member)
    return render(request, 'member_form.html', {'form': form, 'action': 'Edit'})


@login_required
def member_delete(request, pk):
    member = Member.objects.get(pk=pk)
    if request.method == 'POST':
        member.delete()
        return redirect('members_view')
    return render(request, 'member_confirm_delete.html', {'member': member})


# ---------- Ministry CRUD (user-facing) ----------
@login_required
def ministries_list(request):
    # All ministries are viewable
    ministries = Ministry.objects.all().order_by('ministry_name')
    
    # But only certain actions are available based on user's roles
    accessible_ministries = get_user_accessible_ministries(request.user)
    accessible_ministry_ids = list(accessible_ministries.values_list('id', flat=True))
    
    return render(request, 'ministries.html', {
        'ministries': ministries,
        'accessible_ministry_ids': accessible_ministry_ids,
    })


@login_required
def ministry_create(request):
    if request.method == 'POST':
        form = MinistryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ministries')
    else:
        form = MinistryForm()
    return render(request, 'ministry_form.html', {'form': form, 'action': 'Create'})


@login_required
def ministry_edit(request, pk):
    ministry = Ministry.objects.get(pk=pk)
    accessible_ministries = get_user_accessible_ministries(request.user)
    
    # Check if user has permission to edit this ministry
    if ministry not in accessible_ministries:
        return HttpResponseForbidden("You don't have permission to edit this ministry.")
    
    if request.method == 'POST':
        form = MinistryForm(request.POST, instance=ministry)
        if form.is_valid():
            form.save()
            return redirect('ministries')
    else:
        form = MinistryForm(instance=ministry)
    return render(request, 'ministry_form.html', {'form': form, 'action': 'Edit'})


@login_required
def ministry_delete(request, pk):
    ministry = Ministry.objects.get(pk=pk)
    accessible_ministries = get_user_accessible_ministries(request.user)
    
    # Check if user has permission to delete this ministry
    if ministry not in accessible_ministries:
        return HttpResponseForbidden("You don't have permission to delete this ministry.")
    
    if request.method == 'POST':
        ministry.delete()
        return redirect('ministries')
    return render(request, 'ministry_confirm_delete.html', {'ministry': ministry})


# ---------- Attendance Tracking ----------
def attendance_form(request, event_id):
    """
    Public attendance form - no authentication required
    Shows member list filtered by ministry if event has one
    Only accessible within 1 hour before/after event schedule
    """
    from datetime import datetime, timedelta
    import base64
    import io
    
    event = Event.objects.select_related('ministry').prefetch_related('schedules').get(pk=event_id)
    current_dt = datetime.now()
    
    # Check if any schedule is currently accepting attendance (with 1 hour buffer)
    is_accepting = False
    for schedule in event.schedules.all():
        # Get the open and close times
        open_time = schedule.open_time
        close_time = schedule.close_time
        
        # Check if this schedule applies to current date/weekday
        schedule_applies = False
        if schedule.date:
            # One-time event
            if current_dt.date() == schedule.date:
                schedule_applies = True
        elif schedule.weekday is not None:
            # Recurring event
            if current_dt.weekday() == schedule.weekday:
                schedule_applies = True
        
        if schedule_applies:
            # Create datetime objects for open and close times (1 hour buffer)
            open_dt = datetime.combine(current_dt.date(), open_time) - timedelta(hours=1)
            close_dt = datetime.combine(current_dt.date(), close_time) + timedelta(hours=1)
            
            # Handle events that cross midnight
            if close_time < open_time:
                close_dt += timedelta(days=1)
            
            if open_dt <= current_dt <= close_dt:
                is_accepting = True
                break
    
    if not is_accepting:
        # Show "event not active" page
        # Show return button only if user is authenticated (came from events list, not QR scan)
        return render(request, 'event_not_active.html', {
            'event': event,
            'show_return_button': request.user.is_authenticated
        })
    
    # Get members - filter by ministry if event has one
    if event.ministry:
        # Get members of this ministry
        member_ministry_relations = MembersAndMinistries.objects.filter(
            ministry=event.ministry
        ).select_related('member', 'member__family')
        members = [rel.member for rel in member_ministry_relations]
    else:
        # All members
        members = Member.objects.select_related('family').all().order_by('first_name', 'last_name')
    
    context = {
        'event': event,
        'members': members,
    }
    return render(request, 'attendance_form.html', context)


def mark_attendance(request, event_id):
    """
    Process attendance submission - no authentication required
    """
    from datetime import datetime
    from django.contrib import messages
    
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        event = Event.objects.get(pk=event_id)
        member = Member.objects.get(pk=member_id)
        
        # Create or update attendance record (silently handle duplicates)
        attendance, created = Attendance.objects.get_or_create(
            attendee=member,
            event=event,
            defaults={
                'date': datetime.now().date()
            }
        )
        
        if not created:
            # Already marked - update date but show same success message
            attendance.date = datetime.now().date()
            attendance.save()
        
        # Same message whether new or duplicate - don't reveal attendance status
        messages.success(request, 'Attendance recorded successfully!')
        return redirect('attendance_form', event_id=event_id)
    
    return redirect('attendance_form', event_id=event_id)


@login_required
def event_qr_code_data(request, event_id):
    """Return QR code as base64 PNG via JSON for in-page print overlay."""
    import qrcode
    import base64
    from io import BytesIO
    
    event = Event.objects.get(pk=event_id)
    attendance_url = request.build_absolute_uri(reverse('attendance_form', args=[event_id]))
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(attendance_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return JsonResponse({
        'event_name': event.event_name,
        'qr_code': qr_code_base64,
        'attendance_url': attendance_url,
    })


# ---------- Users Management (staff-only) ----------
@login_required
def users_list(request):
    """Users list with search, filters, and bulk actions"""
    from django.contrib.auth.models import User
    from member_management.models import UserProfile, Role, UsersAndRoles, RolesAndMinistries
    
    # Bulk actions
    if request.method == 'POST':
        action = request.POST.get('bulk_action')
        selected_ids = request.POST.get('user_ids', '').split(',')
        if selected_ids and selected_ids[0]:
            users_qs = User.objects.filter(id__in=selected_ids)
            if action == 'delete':
                users_qs.delete()
                return redirect(reverse('users_list') + '?bulk_action=delete')
            elif action == 'deactivate':
                users_qs.update(is_active=False)
                return redirect(reverse('users_list') + '?bulk_action=deactivate')
            elif action == 'activate':
                users_qs.update(is_active=True)
                return redirect(reverse('users_list') + '?bulk_action=activate')
            elif action == 'add_role':
                role_id = request.POST.get('role_id')
                if role_id:
                    role = Role.objects.get(pk=role_id)
                    for user in users_qs:
                        UsersAndRoles.objects.get_or_create(user=user, role=role)
                return redirect(reverse('users_list') + f'?bulk_action=add_role&role_id={role_id}')
            elif action == 'remove_role':
                role_id = request.POST.get('role_id')
                if role_id:
                    UsersAndRoles.objects.filter(user__in=users_qs, role_id=role_id).delete()
                return redirect(reverse('users_list') + f'?bulk_action=remove_role&role_id={role_id}')

    # Queryset
    qs = User.objects.select_related('profile').prefetch_related('user_roles__role').order_by('username')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(profile__member__first_name__icontains=q) |
            Q(profile__member__last_name__icontains=q) |
            Q(profile__member__email__icontains=q)
        )

    # Ministry filter (based on roles' ministry access)
    selected_ministries = request.GET.getlist('ministry')
    if selected_ministries and 'all' not in selected_ministries:
        try:
            mids = [int(x) for x in selected_ministries]
        except ValueError:
            mids = []
        if mids:
            # Get roles that have access to these ministries
            role_ids = RolesAndMinistries.objects.filter(ministry__in=mids).values_list('role_id', flat=True)
            # Get users with these roles
            user_ids = UsersAndRoles.objects.filter(role__in=role_ids).values_list('user_id', flat=True)
            qs = qs.filter(id__in=user_ids)

    # Role filter
    selected_roles = request.GET.getlist('role')
    if selected_roles and 'all' not in selected_roles:
        try:
            rids = [int(x) for x in selected_roles]
        except ValueError:
            rids = []
        if rids:
            user_ids = UsersAndRoles.objects.filter(role__in=rids).values_list('user_id', flat=True)
            qs = qs.filter(id__in=user_ids)

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)
    elif status_filter == 'staff':
        qs = qs.filter(is_staff=True)

    users_list = list(qs)
    
    # Annotate users with their roles (Church Administrator first, then alphabetical)
    from django.db.models import Case, When, Value, IntegerField
    for user in users_list:
        user.role_list = UsersAndRoles.objects.filter(user=user).select_related('role').annotate(
            custom_order=Case(
                When(role__role_name='Church Administrator', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('custom_order', 'role__role_name')

    ministries = Ministry.objects.all().order_by('ministry_name')
    
    # Custom ordering: Church Administrator first, then alphabetical
    roles = Role.objects.all().annotate(
        custom_order=Case(
            When(role_name='Church Administrator', then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('custom_order', 'role_name')

    context = {
        'users': users_list,
        'query': q,
        'ministries': ministries,
        'selected_ministries': selected_ministries,
        'roles': roles,
        'selected_roles': selected_roles,
        'status_filter': status_filter,
    }
    return render(request, 'users.html', context)


@login_required
def user_create(request):
    """Create a new user with password, member association, and roles"""
    from django.contrib.auth.models import User
    from member_management.user_forms import UserCreateForm
    from member_management.models import UsersAndRoles, Role, RolesAndMinistries
    
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # If Admin (staff) is checked, ensure "Church Administrator" role is assigned
            admin_role, _ = Role.objects.get_or_create(role_name="Church Administrator")
            if user.is_staff:
                UsersAndRoles.objects.get_or_create(user=user, role=admin_role)
            
            # Assign other selected roles (Church Administrator may already be assigned above)
            roles = form.cleaned_data.get('roles', [])
            for role in roles:
                UsersAndRoles.objects.get_or_create(user=user, role=role)
            
            return redirect('users_list')
    else:
        form = UserCreateForm()
    
    return render(request, 'user_form.html', {'form': form, 'action': 'Create'})


@login_required
def user_edit(request, pk):
    """Edit an existing user (no password change here)"""
    from django.contrib.auth.models import User
    from member_management.user_forms import UserEditForm
    from member_management.models import UsersAndRoles, Role, RolesAndMinistries
    
    user = User.objects.get(pk=pk)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            # Ensure superuser always has active and admin status
            if user.is_superuser:
                user.is_active = True
                user.is_staff = True
            form.save()
            
            # Handle Admin correlation first
            admin_role, _ = Role.objects.get_or_create(role_name="Church Administrator")
            
            # Update roles: remove all and re-add selected
            UsersAndRoles.objects.filter(user=user).delete()
            
            # If Admin (staff) is checked, ensure Church Administrator is assigned
            if user.is_staff:
                UsersAndRoles.objects.get_or_create(user=user, role=admin_role)
            
            # Assign other selected roles
            roles = form.cleaned_data.get('roles', [])
            for role in roles:
                # Only add Church Administrator from manual selection if staff is NOT checked
                # (to avoid confusion - staff status takes precedence)
                if role == admin_role and user.is_staff:
                    continue  # Already added above
                UsersAndRoles.objects.get_or_create(user=user, role=role)
            
            return redirect('users_list')
    else:
        form = UserEditForm(instance=user)
        # Pre-populate roles
        form.fields['roles'].initial = UsersAndRoles.objects.filter(user=user).values_list('role_id', flat=True)
    
    return render(request, 'user_form.html', {'form': form, 'action': 'Edit', 'user': user})


@login_required
def user_delete(request, pk):
    """Delete a user"""
    from django.contrib.auth.models import User
    
    user = User.objects.get(pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('users_list')
    
    return render(request, 'user_confirm_delete.html', {'user_obj': user})


@login_required
def role_create(request):
    """Create a new role with ministry access"""
    from member_management.user_forms import RoleForm
    from member_management.models import Role, RolesAndMinistries
    
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            
            # Assign ministries
            ministries = form.cleaned_data.get('ministries', [])
            for ministry in ministries:
                RolesAndMinistries.objects.create(role=role, ministry=ministry)
            
            return redirect('users_list')
    else:
        form = RoleForm()
    
    return render(request, 'role_form.html', {'form': form, 'action': 'Create'})


@login_required
def role_edit(request, pk):
    """Edit an existing role and its ministry access"""
    from member_management.user_forms import RoleForm
    from member_management.models import Role, RolesAndMinistries
    
    role = Role.objects.get(pk=pk)
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            # Prevent renaming Church Administrator role
            if role.role_name == "Church Administrator" and form.cleaned_data.get('role_name') != "Church Administrator":
                # keep original name
                form.instance.role_name = "Church Administrator"
                form.save()
            else:
                form.save()
            
            # Update ministries: remove all and re-add selected
            RolesAndMinistries.objects.filter(role=role).delete()
            ministries = form.cleaned_data.get('ministries', [])
            for ministry in ministries:
                RolesAndMinistries.objects.create(role=role, ministry=ministry)
            
            return redirect('users_list')
    else:
        form = RoleForm(instance=role)
    
    return render(request, 'role_form.html', {'form': form, 'action': 'Edit', 'role': role})


@login_required
def role_delete(request, pk):
    """Delete a role"""
    from member_management.models import Role
    
    role = Role.objects.get(pk=pk)
    # Protect Church Administrator from deletion
    if role.role_name == "Church Administrator":
        return redirect('users_list')
    if request.method == 'POST':
        role.delete()
        return redirect('users_list')
    
    return render(request, 'role_confirm_delete.html', {'role': role})


# ---------- Event CRUD (user-facing) ----------