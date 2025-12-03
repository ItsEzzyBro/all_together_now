# ⛪️ All Together Now: A Church Membership Database

A church membership database that organizes and manages the information of members and visitors in a church congregation

## 📋 Table of Contents

- [Abstract](#abstract)
- [Project Components](#project-components)
- [Technology Stack](#technology-stack)

## 🫂 Abstract

A problem most small to medium size churches have is managing their church congregation and following up with visitors. All Together Now is a church membership database that will organize and manage the information of members and visitors in a church congregation. This database will give small to medium sized churches a better way of organizing and structuring their congregation and to give them a better idea of the health of the church in terms of membership. Through this database, churches are able to add new member or visitor information, edit and update existing member information, group members into different ministries or church groups, have a digital attendance check-in for members, and track member attendance. This will allow churches to reach out to members or visitors (which will help with mentoring, contacting/outreach, and other needs that the church may have), have more structure in ministries/church groups, keep track of congregation growth, as well as to make it easier to take and track attendance.

## 🧑‍🧑‍🧒 Project Components

### Member Management

- **Member Database**: To hold and organize member information
  - Security and privacy concerns will be kept in mind
- **User Login**: To establish user roles among ministry leaders to access the database
  - Ministry leaders will be allowed to make their own password
  - Depending on the ministry/role/job, they will have access to/view certain information
  - They will be able to edit the members and their information within their ministry/group
  - Two-Step Verification for extra security
- **Create visitor connection cards and send/forward them to the appropriate ministry leader(s)**
  - QR Code and Form Usage

### Attendance and Group Tracking

- **Ministry/Church Grouping**: Groups members of the congregation into their respected ministry/church group
  - Also includes the board/leadership members of that ministry/group
- **Attendance Check-In for Members**
  - QR Code and Form Usage

### Reporting and Analytics

- **Search and Filter**: Allows users to find members and families based off name, ministry/group, or characteristics
- **Attendance Tracker**: Tracks church or group attendance, which can be filtered based on certain intervals of time

## 🖥️ Technology Stack

The Technology stack we will be using to implement the project components above is PostgreSQL for the database to store and organize member and visitor information, Django for the backend to communicate and retrieve the information from the database to display to the user, Django templates for the frontend to display and visualize the information from the database in a user-friendly and visually appealing way. We will also be using the Google Cloud Platform as the Cloud Platform to make this project live in the cloud.
