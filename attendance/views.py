from django.shortcuts import render, redirect, get_object_or_404
from .models import Member
from django.http import HttpResponse
from datetime import date
from .models import Member, Attendance, NewMember
from django.contrib import messages
import re, io, os
from datetime import date, timedelta
import pandas as pd
from django.db.models import Prefetch
from django.db.models.functions import ExtractYear, ExtractMonth
from dotenv import load_dotenv
from .constants import DEPARTMENTS

# Create your views here.
load_dotenv()

CHILD_PASSCODE = os.environ.get("CHILD_PASSCODE") 
TEEN_PASSCODE = os.environ.get("TEEN_PASSCODE")
WORKER_PASSCODE = os.environ.get("WORKER_PASSCODE")
ADMIN_PASSCODE = os.environ.get("ADMIN_PASSCODE")


def check_passcode(request):
    if request.method == "POST":
        entered_code = request.POST.get("passcode")

        if entered_code == CHILD_PASSCODE:
            request.session['access_level'] = 'children'
            return redirect('home')
        elif entered_code == TEEN_PASSCODE:
            request.session['access_level'] = 'teens'
            return redirect('home')
        elif entered_code == WORKER_PASSCODE:
            request.session['access_level'] = 'workers'
            return redirect('home')
        elif entered_code == ADMIN_PASSCODE:
            request.session['access_level'] = 'admin'
            return redirect('home')
        else:
            return render(request, "attendance/passcode.html", {"error": "Invalid passcode"})
    return render(request, "attendance/passcode.html")


def logout_user(request):
    request.session.flush()
    return redirect('check_passcode')


from django.db.models import Q

def home(request):
    access = request.session.get('access_level')
    if not access:
        return redirect('check_passcode')  # force passcode first

    query = request.GET.get("q", "").strip()

    # Base queryset filtered by access level
    members = Member.objects.all()
    if access == 'children':
        members = members.filter(role__iexact='Child')
    elif access == 'teens':
        members = members.filter(role__iexact='Teen')
    elif access == 'workers':
        members = members.filter(role__iexact='worker')

    # Apply search if query exists
    if query:
        if query.isdigit():
            members = members.filter(serial_number__icontains=query)
        else:
            members = members.filter(name__icontains=query)
    else:
        members = members.none()  # Hide all if no query

    # Prefetch today’s attendance
    today = date.today()
    members = members.prefetch_related(
        Prefetch('attendance_set', queryset=Attendance.objects.filter(date=today))
    )

    for m in members:
        m.today_marked = m.attendance_set.exists()

    context = {
        "members": members,
        "query": query
    }

    return render(request, "attendance/index.html", context)

def mark_present(request, member_id):
    access = request.session.get('access_level')
    if not access:
        return redirect('check_passcode')  # force passcode first
    

    member = get_object_or_404(Member, id=member_id)

    if request.method == "POST":
        attendance_exists = Attendance.objects.filter(
            member=member,
            date=date.today(),
            service_type="first"
        ).exists()

        if attendance_exists:
            messages.error(request, "Already marked present!")
        else:
            Attendance.objects.create(
                member=member,
                date=date.today(),
                service_type="first"
            )
            messages.success(request, "Marked present successfully!")

        # ALWAYS redirect after POST
        return redirect("home")

    return redirect("home")



def new_member(request):
    access = request.session.get('access_level')
    if access != 'admin':
        messages.error(request, "You are not an admin!")
        return redirect('home')

    member = None   # safe default

    if request.method == "POST":
        name = request.POST.get("name")
        role = request.POST.get("role")
        phone_number = request.POST.get("phone")

        if NewMember.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "New member already exists!")
            return render(request, "attendance/newcomer.html")

        # Create member
        member = NewMember.objects.create(
            name=name,
            role=role,
            phone_number=phone_number
        )

        messages.success(request, "New member saved successfully!")

    return render(request, "attendance/newcomer.html", {"member": member})


def existing_member(request):
    access = request.session.get('access_level')
    if access != 'admin':
        messages.error(request, "You are not an admin!")
        return redirect('home')
    
    member = None
    attendance_marked = False
    save_only_message = None
    error = None
    message = None

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        role = request.POST.get("role")
        phone_number = request.POST.get("phone_number")
        parent_phone_number = request.POST.get("parent_phone")
        parent_name = request.POST.get("parent_name")
        department = request.POST.get("department")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        status_complete = True

        try:
            age = int(age)
        except ValueError:
            age = None
            status_complete = False

        phone_pattern = re.compile(r"^[0-9 \-()+]{6,}$")

        if not name:
            message = messages.error(request, "Name is required!")
            return render(request, "attendance/existing_member.html", {"name": name})
        
        if not role:
            message = messages.error(request, "Select a role!")
            return render(request, "attendance/existing_member.html", {"name": name})    
        
        if role == 'Child':
            required_fields = [parent_name, parent_phone_number, age]
            if any(not f for f in required_fields) or not phone_pattern.fullmatch(parent_phone_number or ""):
                status_complete = False
                parent_name = parent_name or '--'
                parent_phone_number = parent_phone_number or '--'
                age = age or None
        elif role == 'Teen':
            if not phone_number or not phone_pattern.fullmatch(phone_number):
                status_complete = False
                phone_number = phone_number or '--'
        elif role == 'Worker':
            if not phone_number or not phone_pattern.fullmatch(phone_number) or not department:
                status_complete = False
                phone_number = phone_number or '--'
                department = department or '--'

        if Member.objects.filter(name=name):
            message = messages.error(request, "Member already exists!")
            return render(request, "attendance/existing_member.html", {"message": message})
        else:
            member = Member.objects.create(
                name=name,
                role=role,
                phone_number=phone_number,
                department=department,
                parent_name=parent_name,
                parent_phone_number=parent_phone_number,
                age=age,
                gender = gender,
                status_complete=status_complete
            )
            message = messages.success(request, "New member saved successfully!")

        try:
            attendance, created = Attendance.objects.get_or_create(
                member=member,
                date=date.today(),
                service_type="first"
            )
            if created:
                attendance_marked = True
            else:
                save_only_message = "Member saved. Attendance for today already exists. Please mark present from the search tab if needed."
        except Exception:
            # In case something fails during attendance marking
            save_only_message = "Member saved but could not mark attendance. Please mark present from the search tab."

    return render(request, "attendance/existing_member.html", {
        "member": member,
        "attendance_marked": attendance_marked,
        "save_only_message": save_only_message,
        "error": error,
        "message": message
    })

def valid_phone(phone):
    """Accept only digits, 10–15 length."""
    if not phone:
        return False
    return bool(re.fullmatch(r"\d{10,15}", phone))


def complete_profile(request):
    access = request.session.get('access_level')
    if access != 'admin':
        messages.error(request, "You are not an admin!")
        return redirect('home')
    

    members = Member.objects.filter(status_complete=False)
    selected_member = None

    def render_context():
        return render(request, "attendance/complete_profile.html", {
            "members": members,
            "departments": DEPARTMENTS,
            "selected_member": selected_member,
        })

    if request.method == "POST":
        member_id = request.POST.get("member")
        print(request.POST)
        if member_id:
            selected_member = get_object_or_404(Member, id=member_id)

        # SEARCH BUTTON
        if "search_member" in request.POST:
            return render_context()

        # SAVE PROFILE BUTTON
        elif "save_profile" in request.POST:
            selected_member = get_object_or_404(Member, id=member_id)
            role = request.POST.get("role").lower()

            # Map fields based on role (role is already lowercased)
            if role in ["child", "children"]:
                parent_name = (request.POST.get("parent_name") or "").strip()
                parent_phone = (request.POST.get("parent_phone") or "").strip()
                age = (request.POST.get("age") or "").strip()
                gender = (request.POST.get("gender_child") or "").strip()

                if not parent_name:
                    messages.error(request, "Parent name is required.")
                    return render(request, "attendance/complete_profile.html", {
                        "members": members,
                        "departments": DEPARTMENTS,
                        "selected_member": selected_member,
                    })
                if not parent_phone or not valid_phone(parent_phone):
                    messages.error(request, "Enter a valid parent phone number (10–15 digits).")
                    return render(request, "attendance/complete_profile.html", {
                        "members": members,
                        "departments": DEPARTMENTS,
                        "selected_member": selected_member,
                    })
                if not age:
                    messages.error(request, "Age is required.")
                    return render(request, "attendance/complete_profile.html", {
                        "members": members,
                        "departments": DEPARTMENTS,
                        "selected_member": selected_member,
                    })
                if not gender:
                    messages.error(request, "Gender is required.")
                    return render(request, "attendance/complete_profile.html", {
                        "members": members,
                        "departments": DEPARTMENTS,
                        "selected_member": selected_member,
                    })

                selected_member.parent_name = parent_name
                selected_member.parent_phone_number = parent_phone
                selected_member.age = int(age)
                selected_member.gender = gender

            elif role == "teen":
                phone = (request.POST.get("phone_teen") or "").strip()
                gender = (request.POST.get("gender_teen") or "").strip()

                if not phone or not valid_phone(phone):
                    messages.error(request, "Enter a valid phone number (10–15 digits).")
                    return render(request, "attendance/complete_profile.html", {
                        "members": members,
                        "departments": DEPARTMENTS,
                        "selected_member": selected_member,
                    })
                if not gender:
                    messages.error(request, "Gender is required.")
                    return render(request, "attendance/complete_profile.html", {
                        "members": members,
                        "departments": DEPARTMENTS,
                        "selected_member": selected_member,
                    })

                selected_member.phone_number = phone
                selected_member.gender = gender

            elif role == "worker":
                phone = (request.POST.get("phone_worker") or "").strip()
                gender = (request.POST.get("gender_worker") or "").strip()
                department = (request.POST.get("department") or "").strip()

                if not phone or not valid_phone(phone):
                    messages.error(request, "Enter a valid phone number (10–15 digits).")
                    return render(request, "attendance/complete_profile.html", {
                        "members": members,
                        "departments": DEPARTMENTS,
                        "selected_member": selected_member,
                    })
                if not gender:
                    messages.error(request, "Gender is required.")
                    return render(request, "attendance/complete_profile.html", {
                        "members": members,
                        "departments": DEPARTMENTS,
                        "selected_member": selected_member,
                    })
                if not department:
                    messages.error(request, "Department is required.")
                    return render(request, "attendance/complete_profile.html", {
                        "members": members,
                        "departments": DEPARTMENTS,
                        "selected_member": selected_member,
                    })

                selected_member.phone_number = phone
                selected_member.gender = gender
                selected_member.department = department

            # Common fields
            selected_member.role = request.POST.get("role")
            selected_member.status_complete = True
            selected_member.save()

            messages.success(request, "Member Profile updated successfully!")
            return redirect("complete_profile")

    return render_context()


def admin(request):
    access = request.session.get('access_level')
    if access != 'admin':
        messages.error(request, "You are not an admin!")
        return redirect('home')


    members = Member.objects.filter(status_complete=False)

    # Get POST data
    selected_role = request.POST.get("role") if request.method=="POST" else ""
    selected_department = request.POST.get("department") if request.method=="POST" else ""
    selected_year = int(request.POST.get("year")) if request.method=="POST" and request.POST.get("year") else None
    selected_month = int(request.POST.get("month")) if request.method=="POST" and request.POST.get("month") else None

    error_message = None

    # Get available years efficiently using database aggregation
    available_years = list(
        Attendance.objects.annotate(year=ExtractYear('date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('year')
    )

    # Dynamic months based on selected year using database aggregation
    if selected_year:
        available_months = list(
            Attendance.objects.filter(date__year=selected_year)
            .annotate(month=ExtractMonth('date'))
            .values_list('month', flat=True)
            .distinct()
            .order_by('month')
        )
    else:
        available_months = list(
            Attendance.objects.annotate(month=ExtractMonth('date'))
            .values_list('month', flat=True)
            .distinct()
            .order_by('month')
        )

    # Filter members by role and department
    if selected_role:
        members = members.filter(role=selected_role)
        if selected_role == "Worker":
            if selected_department:
                members = members.filter(department=selected_department.upper())
            else:
                members = members.none()
                error_message = "Please select a department for Worker role."

    # Validate selected year/month
    if selected_year and selected_year not in available_years:
        error_message = "No attendance records for selected year."
        members = members.none()
        selected_month = None
    if selected_month and selected_month not in available_months:
        error_message = "No attendance records for selected month."
        members = members.none()

    # Generate Sundays for selected month/year
    attendance_dates = []

    if selected_year:
        # Determine months to include
        if selected_month:
            months_to_check = [selected_month]  # Only the selected month
        else:
            # All months that have attendance in that year (reuse available_months)
            months_to_check = available_months

        # Loop through each month to get Sundays
        for month in months_to_check:
            first_day = date(selected_year, month, 1)
            i = 0
            while True:
                current_day = first_day + timedelta(days=i)
                if current_day.month != month:
                    break
                if current_day.weekday() == 6:  # Sunday
                    attendance_dates.append(current_day)
                i += 1

    attendance_dates.sort()  # Optional: to keep in chronological order

    # Prefetch attendance for the date range to avoid N+1 queries
    if attendance_dates:
        members = members.prefetch_related(
            Prefetch(
                'attendance_set',
                queryset=Attendance.objects.filter(date__in=attendance_dates),
                to_attr='prefetched_attendance'
            )
        )

    # Attach attendance marks efficiently using prefetched data
    for member in members:
        attended_dates = {att.date for att in getattr(member, 'prefetched_attendance', [])}
        member.marks = [sunday in attended_dates for sunday in attendance_dates]

    return render(request, "attendance/admin.html", {
        "members": members,
        "attendance_dates": attendance_dates,
        "departments": DEPARTMENTS,
        "selected_role": selected_role,
        "selected_department": selected_department,
        "selected_year": selected_year,
        "selected_month": selected_month,
        "years": available_years,
        "months": available_months,
        "error_message": error_message,
    })


def build_member_row(member, role, attendance_dates, serial):
    """
    Returns a list representing a member's row for Excel export.
    Handles different roles dynamically.
    """
    row = [serial]  # Serial number

    if role == "Child":
        row += [
            member.name,
            member.age,
            member.role,
            member.gender,
            member.parent_phone,
            member.parent_name
        ]
    elif role == "Teen":
        row += [
            member.name,
            member.phone_number,
            member.gender,
            member.role
        ]
    elif role == "Worker":
        row += [
            member.name,
            member.phone_number,
            member.role,
            member.gender,
            member.department
        ]
    elif role == "New_Member":
        row += [
            member.name,
            member.phone_number,
            member.role,
            member.date_joined
        ]
    else:  # general/full download
        row += [
            member.name,
            getattr(member, "parent_phone", "---"),
            getattr(member, "gender", "---"),
            getattr(member, "parent_phone", "---"),
            getattr(member, "phone", "---"),
            getattr(member, "age", "---"),
            getattr(member, "department", "---"),
            member.role
        ]

    # Append attendance marks if not a new member
    if role != "New_Member":
        attended_dates = {att.date for att in member.attendance_set.all()}
        for sunday in attendance_dates:
            row.append("✅" if sunday in attended_dates else "---")

    return row

def download_page(request):
    # access = request.session.get('access_level')
    # if not access:
    #     return redirect('check_passcode')  # force passcode first

    today = date.today()
    return render(request, "attendance/download.html", {
        "departments": DEPARTMENTS,
        "selected_year": today.year,
        "selected_month": today.month,
        "selected_role": "",
        "selected_department": "",
    })



def download(request):
    selected_role = request.POST.get("role") if request.method=="POST" else ""
    selected_department = request.POST.get("department") if request.method=="POST" else ""
    selected_year = None
    selected_month = None

    if request.method == "POST" and request.POST.get("month"):
        year, month = map(int, request.POST.get("month").split("-"))
        selected_year = year
        selected_month = month

    error_message = None
    success_message = None

    # Get available years efficiently using database aggregation
    available_years = list(
        Attendance.objects.annotate(year=ExtractYear('date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('year')
    )
    
    # Get available months using database aggregation
    if selected_year:
        available_months = list(
            Attendance.objects.filter(date__year=selected_year)
            .annotate(month=ExtractMonth('date'))
            .values_list('month', flat=True)
            .distinct()
            .order_by('month')
        )
    else:
        available_months = list(
            Attendance.objects.annotate(month=ExtractMonth('date'))
            .values_list('month', flat=True)
            .distinct()
            .order_by('month')
        )

    access = request.session.get('access_level')

    if access != "admin":
        error_message = "You are not allowed to download files!"
        return render(request, "attendance/download.html", {
            "departments": DEPARTMENTS,
            "selected_role": selected_role,
            "selected_department": selected_department,
            "selected_year": selected_year,
            "selected_month": selected_month,
            "error_message": error_message
        })
    
    
    # Generate Sundays for the selected month/year
    attendance_dates = []
    if selected_year:
        if selected_month:
            first_day = date(selected_year, selected_month, 1)
            i = 0
            while True:
                current_day = first_day + timedelta(days=i)
                if current_day.month != selected_month:
                    break
                if current_day.weekday() == 6:  # Sunday
                    attendance_dates.append(current_day)
                i += 1
        else:
            error_message = "Please select a month/year!"

    attendance_dates.sort()



        # Admin can see all
    if selected_role == "Child":
        members = Member.objects.filter(role__iexact="Child")
    elif selected_role == "Teen":
        members = Member.objects.filter(role__iexact="Teen")
    elif selected_role == "Worker":
        members = Member.objects.filter(role__iexact="Worker")
    elif selected_role == "New_Member":
        members = NewMember.objects.all()
    else:
        members = Member.objects.all()
            

    # Get members based on role and department
    if selected_role == "Worker" and selected_department:
        members = members.filter(department__iexact=selected_department)

    # --- Correct attendance check per role ---
    if selected_role != "New_Member":
        attendance_exists = Attendance.objects.filter(
            date__year=selected_year,
            date__month=selected_month,
            member__in=members
        ).exists()
    else:
        attendance_exists = members.filter(
            date_joined__year=selected_year,
            date_joined__month=selected_month
        ).exists()

    if not attendance_exists:
        error_message = f"No {selected_role} attendance found for {selected_month}-{selected_year}!"
        return render(request, "attendance/download.html", {
            "departments": DEPARTMENTS,
            "selected_role": selected_role,
            "selected_department": selected_department,
            "selected_year": selected_year,
            "selected_month": selected_month,
            "error_message": error_message
        })


    # if selected_role == "Worker" and not selected_department:
    #     error_message = "Please select a department for Worker role!"
    #     return render(request, "attendance/download.html", {
    #         "departments": departments,
    #         "selected_role": selected_role,
    #         "selected_department": selected_department,
    #         "error_message": error_message,
    #         "selected_year": selected_year,
    #         "selected_month": selected_month,
    #     })

    # Prefetch attendance for optimization
    if selected_role != "New_Member":
        members = members.prefetch_related(
            Prefetch(
                'attendance_set',
                queryset=Attendance.objects.filter(date__in=attendance_dates)
            )
        )

    # Build headers
    if selected_role == "Child":
        headers = ["S/N", "Name", "Age", "Role", "Gender", "Parent Number", "Parent Name"]
    elif selected_role == "Teen":
        headers = ["S/N", "Name", "Phone Number", "Gender", "Role"]
    elif selected_role == "Worker":
        headers = ["S/N", "Name", "Phone Number", "Role", "Gender", "Department"]
    elif selected_role == "New_Member":
        headers = ["S/N", "Name", "Phone", "Role", "Date Joined"]
    else:
        headers = ["S/N", "Name", "Parent Number", "Gender", "Parent Phone", "Phone", "Age", "Department", "Role"]

    # Format Sundays nicely
    headers += [day.strftime("%d-%b-%Y") for day in attendance_dates]

    # Build rows
    rows = [build_member_row(member, selected_role, attendance_dates, i) for i, member in enumerate(members, start=1)]

    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)

    try:
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        role_for_file = selected_role if selected_role else "all_members"
        response['Content-Disposition'] = f'attachment; filename="{role_for_file}_attendance_{selected_year}_{selected_month}.xlsx"'
        return response
    except Exception as e:
        error_message = f"Unable to download attendance! Error: {e}"

    return render(request, "attendance/download.html", {
        "members": members,
        "attendance_dates": attendance_dates,
        "departments": DEPARTMENTS,
        "selected_role": selected_role,
        "selected_department": selected_department,
        "selected_year": selected_year,
        "selected_month": selected_month,
        "years": available_years,
        "months": available_months,
        "error_message": error_message,
        "success_message": success_message
    })