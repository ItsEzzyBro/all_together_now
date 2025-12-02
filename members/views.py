# members/views.py
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from member_management.models import Member, Family, Vistor
from django.db.models import Q
from datetime import date
from ministry.models import Ministry, MembersAndMinistries
from member_management.forms import MemberForm, FamilyForm, VistorForm
from ministry.forms import MinistryForm

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
def attendance_view(request):
    return render(request, "attendance.html")

@login_required
def analytics_view(request):
    return render(request, "analytics.html")

@login_required
def system_view(request):
    return render(request, "system.html")

@login_required
def profile(request):
    # You can create a dedicated template later; using dashboard for now
    return render(request, "dashboard.html")

@login_required
def change_password(request):
    # You can wire Django's PasswordChangeView later; placeholder template for now
    return render(request, "dashboard.html")


# ---------- Member CRUD (user-facing) ----------
@login_required
def members_list(request):
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
                if ministry_id:
                    ministry = Ministry.objects.get(pk=ministry_id)
                    for member in members_qs:
                        MembersAndMinistries.objects.get_or_create(member=member, ministry=ministry)
                # Redirect back keeping the selected ministry and action in the URL
                return redirect(reverse('members_view') + f'?bulk_action=add_to_ministry&ministry_id={ministry_id}')
            elif action == 'remove_from_ministry':
                ministry_id = request.POST.get('ministry_id')
                if ministry_id:
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

    # Queryset
    qs = Member.objects.all().order_by('last_name', 'first_name')

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

    # available ministries for UI
    ministries = Ministry.objects.all().order_by('ministry_name')
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
    ministries = Ministry.objects.all().order_by('ministry_name')
    return render(request, 'ministries.html', {'ministries': ministries})


@login_required
def ministry_create(request):
    if request.method == 'POST':
        form = MinistryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ministries_list')
    else:
        form = MinistryForm()
    return render(request, 'ministry_form.html', {'form': form, 'action': 'Create'})


@login_required
def ministry_edit(request, pk):
    ministry = Ministry.objects.get(pk=pk)
    if request.method == 'POST':
        form = MinistryForm(request.POST, instance=ministry)
        if form.is_valid():
            form.save()
            return redirect('ministries_list')
    else:
        form = MinistryForm(instance=ministry)
    return render(request, 'ministry_form.html', {'form': form, 'action': 'Edit'})


@login_required
def ministry_delete(request, pk):
    ministry = Ministry.objects.get(pk=pk)
    if request.method == 'POST':
        ministry.delete()
        return redirect('ministries_list')
    return render(request, 'ministry_confirm_delete.html', {'ministry': ministry})


@login_required
def create_event(request, pk):
    # Placeholder create-event view for a ministry. For now render a small form placeholder.
    ministry = Ministry.objects.get(pk=pk)
    if request.method == 'POST':
        # Implement event creation logic later; redirect back to ministries
        return redirect('ministries_list')
    return render(request, 'create_event.html', {'ministry': ministry})
