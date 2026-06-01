from django.shortcuts import render, redirect
from .models import Customer
from django.db.models import Q
from django.core.paginator import Paginator
from io import BytesIO
import pandas as pd
import re


EDIT_USER_IDS = {
    'CB-SA-ADMIN01',
    'CB-SA-ADMIN02',
}

USER_PASSWORDS = {
    'CB-SA-ADMIN01': 'Carrington@555',
    'CB-SA-ADMIN02': 'Carrington@555',
    'CB-SA-001': 'Admin@123',
    'CB-SA-002': 'Admin@123',
    'CB-SA-003': 'Admin@123',
    'CB-SA-004': 'Admin@123',
    'CB-SA-005': 'Admin@123',
    'CB-SA-006': 'Admin@123',
    'CB-SA-007': 'Admin@123',
    'CB-SA-008': 'Admin@123',
    'CB-SA-009': 'Admin@123',
    'CB-SA-010': 'Admin@123',
}


def normalize_excel_column(name):
    cleaned = re.sub(r'[^a-z0-9]+', '_', str(name).strip().lower()).strip('_')
    return cleaned


def import_customers_from_excel(file_obj):
    df = pd.read_excel(BytesIO(file_obj.read()))
    df = df.dropna(how='all')
    if df.empty:
        return 0

    normalized_columns = {col: normalize_excel_column(col) for col in df.columns}
    df = df.rename(columns=normalized_columns)

    field_aliases = {
        'mobile': 'mobile',
        'mobile_no': 'mobile',
        'phone': 'mobile',
        'customer_name': 'customer_name',
        'name': 'customer_name',
        'customer': 'customer_name',
        'father_name': 'father_name',
        'father': 'father_name',
        'alt_number': 'alt_number',
        'alternate_number': 'alt_number',
        'dob': 'dob',
        'date_of_birth': 'dob',
        'local_address': 'local_address',
        'address': 'local_address',
        'permanent_address': 'permanent_address',
        'aadhar_pan': 'aadhar_pan',
        'pan': 'aadhar_pan',
        'govt_id_pan': 'aadhar_pan',
        'email': 'email',
    }

    mapped_columns = {}
    for col in df.columns:
        mapped_col = field_aliases.get(col)
        if mapped_col:
            mapped_columns[col] = mapped_col

    saved_count = 0
    for _, row in df.iterrows():
        mobile = str(row.get('mobile') or '').strip()
        if not mobile:
            continue

        data = {}
        for col, mapped_col in mapped_columns.items():
            value = row[col]
            if pd.isna(value):
                value = ''
            data[mapped_col] = str(value).strip()

        required_fields = ['customer_name', 'mobile']
        if not all(data.get(field) for field in required_fields):
            continue

        Customer.objects.update_or_create(
            mobile=mobile,
            defaults={
                'customer_name': data.get('customer_name', ''),
                'father_name': data.get('father_name', ''),
                'alt_number': data.get('alt_number', ''),
                'dob': data.get('dob', ''),
                'local_address': data.get('local_address', ''),
                'permanent_address': data.get('permanent_address', ''),
                'aadhar_pan': data.get('aadhar_pan', ''),
                'email': data.get('email', ''),
            }
        )
        saved_count += 1

    return saved_count


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username') or request.POST.get('email')
        password = request.POST.get('password')

        stored_password = USER_PASSWORDS.get(username)
        if stored_password and stored_password == password:
            request.session['username'] = username
            request.session['can_edit'] = username in EDIT_USER_IDS
            request.session['is_authenticated'] = True
            return redirect('home')

        return render(request, 'login.html', {
            'error_message': 'Invalid user ID or password.'
        })

    return render(request, 'login.html')


def home(request):
    import_message = None
    delete_message = None
    logged_in_user = request.session.get('username')
    can_edit = bool(request.session.get('can_edit')) and logged_in_user in EDIT_USER_IDS
    user_role = 'Editor' if can_edit else 'Viewer'

    if request.method == 'POST':
        if not can_edit:
            import_message = 'You have view-only access. Upload and delete actions are disabled.'
        elif request.FILES.get('excel_file'):
            try:
                saved_count = import_customers_from_excel(request.FILES['excel_file'])
                import_message = f'Successfully imported {saved_count} record(s).' if saved_count else 'No valid rows found in the uploaded file.'
            except Exception as exc:
                import_message = f'Upload failed: {exc}'
        elif request.POST.get('delete_id'):
            try:
                customer = Customer.objects.get(id=request.POST.get('delete_id'))
                customer.delete()
                delete_message = 'Record deleted successfully.'
            except Customer.DoesNotExist:
                delete_message = 'Record not found.'

    query_set = Customer.objects.order_by('id')

    # Sidebar main name search
    search_query = request.GET.get('search')
    if search_query:
        query_set = query_set.filter(customer_name__icontains=search_query)

    # Top contextual filters
    filter_name = request.GET.get('filter_name')
    if filter_name:
        query_set = query_set.filter(customer_name__icontains=filter_name)

    filter_address = request.GET.get('filter_address')
    if filter_address:
        query_set = query_set.filter(
            Q(local_address__icontains=filter_address) | 
            Q(permanent_address__icontains=filter_address)
        )
    filter_mobile = request.GET.get('filter_mobile')
    if filter_mobile:
        query_set = query_set.filter(mobile__icontains=filter_mobile)

    # Universal field "Search Any Field" search
    filter_any = request.GET.get('filter_any')
    if filter_any:
        query_set = query_set.filter(
            Q(customer_name__icontains=filter_any) |
            Q(email__icontains=filter_any) |
            Q(mobile__icontains=filter_any)
        )

    paginator = Paginator(query_set, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)

    context = {
        'all_data': page_obj,
        'page_obj': page_obj,
        'query_string': query_params.urlencode(),
        'import_message': import_message,
        'delete_message': delete_message,
        'can_edit': can_edit,
        'logged_in_user': logged_in_user,
        'user_role': user_role,
    }
    return render(request, 'home.html', context)
