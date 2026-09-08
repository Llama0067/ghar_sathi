from nicegui import app, ui
import database as db

db.init_db()

# Application state stored in session memory
class State:
    def __init__(self):
        self.user = None
        self.role = None
        self.fullname = None
        self.specialty = None

session = State()

# --- UI PAGES ---

@ui.page('/')
def login_page():
    session.user = None  # Reset session on login page
    
    with ui.card().classes('w-96 absolute-center p-6 shadow-28 rounded-lg'):
        ui.label('CareConnect').classes('text-3xl font-bold text-primary text-center w-full')
        ui.label('Desktop Caregiver Portal').classes('text-sm text-gray-500 text-center w-full mb-4')

        with ui.tabs().classes('w-full') as tabs:
            login_tab = ui.tab('Login')
            register_tab = ui.tab('Register')

        with ui.tab_panels(tabs, value=login_tab).classes('w-full mt-4'):
            # LOGIN PANEL
            with ui.tab_panel(login_tab):
                username_input = ui.input('Username').classes('w-full')
                password_input = ui.input('Password', password=True, password_toggle_button=True).classes('w-full')
                
                def handle_login():
                    u = username_input.value.strip()
                    p = password_input.value.strip()
                    res = db.authenticate_user(u, p)
                    if res:
                        session.user = u
                        session.role, session.specialty, session.fullname = res
                        if session.role == 'user':
                            ui.navigate.to('/client')
                        else:
                            ui.navigate.to('/worker')
                    else:
                        ui.notify('Invalid username or password', type='negative')

                ui.button('Login to Portal', on_click=handle_login).classes('w-full mt-4')

            # REGISTER PANEL
            with ui.tab_panel(register_tab):
                reg_fullname = ui.input('Full Name').classes('w-full')
                reg_username = ui.input('Username').classes('w-full')
                reg_password = ui.input('Password', password=True).classes('w-full')
                
                role_select = ui.select({'user': 'Client / Family', 'worker': 'Caregiver Worker'}, value='user', label='Role').classes('w-full')
                specialty_select = ui.select(['Babysitting', 'Elderly Care', 'Pet Care'], value='Babysitting', label='Specialty').classes('w-full')
                specialty_select.bind_visibility_from(role_select, 'value', value='worker')

                def handle_register():
                    fn = reg_fullname.value.strip()
                    u = reg_username.value.strip()
                    p = reg_password.value.strip()
                    r = role_select.value
                    s = specialty_select.value if r == 'worker' else None

                    if not fn or not u or not p:
                        ui.notify('Please fill in all required fields.', type='warning')
                        return

                    success, msg = db.register_user(u, p, fn, r, s)
                    if success:
                        ui.notify(msg, type='positive')
                        tabs.set_value(login_tab)
                    else:
                        ui.notify(msg, type='negative')

                ui.button('Create Account', on_click=handle_register).classes('w-full mt-4')


def render_sidebar(role_title):
    with ui.left_drawer(value=True).classes('bg-slate-800 text-white p-4 w-64'):
        ui.label('CareConnect').classes('text-2xl font-bold')
        ui.label(role_title).classes('text-xs text-gray-400 mb-6')
        
        with ui.card().classes('bg-slate-700 p-3 text-white w-full mb-6'):
            ui.label(session.fullname or 'User').classes('font-bold text-sm')
            ui.label(f'@{session.user}').classes('text-xs text-gray-300')

        ui.element('div').classes('flex-grow')
        ui.button('Logout', color='negative', on_click=lambda: ui.navigate.to('/')).classes('w-full')


@ui.page('/client')
def client_dashboard():
    if not session.user or session.role != 'user':
        ui.navigate.to('/')
        return

    render_sidebar('Client Portal')

    with ui.column().classes('w-full p-6'):
        ui.label('Client Dashboard').classes('text-2xl font-bold mb-4')

        with ui.row().classes('w-full gap-6 items-start'):
            # Left Column: Booking Form
            with ui.card().classes('w-80 p-4 shadow-md'):
                ui.label('Book Care Service').classes('text-lg font-bold mb-2')
                
                service_opt = ui.select(['Babysitting', 'Elderly Care', 'Pet Care'], value='Babysitting', label='Category').classes('w-full')
                datetime_in = ui.input('Date & Time', placeholder='Oct 24, 2:00 PM - 6:00 PM').classes('w-full')
                notes_in = ui.textarea('Additional Details / Requirements').classes('w-full')

                def submit_request():
                    if not datetime_in.value.strip() or not notes_in.value.strip():
                        ui.notify('Please complete all details.', type='warning')
                        return
                    db.create_booking(session.user, service_opt.value, datetime_in.value.strip(), notes_in.value.strip())
                    ui.notify('Booking request submitted!', type='positive')
                    datetime_in.value = ''
                    notes_in.value = ''
                    refresh_bookings()

                ui.button('Submit Request', on_click=submit_request).classes('w-full mt-4')

            # Right Column: Bookings History
            with ui.card().classes('flex-1 p-4 shadow-md'):
                ui.label('My Booking Requests').classes('text-lg font-bold mb-4')
                bookings_container = ui.column().classes('w-full gap-3')

                def refresh_bookings():
                    bookings_container.clear()
                    bookings = db.fetch_client_bookings(session.user)
                    
                    if not bookings:
                        with bookings_container:
                            ui.label('No requests placed yet. Use the form on the left to create one.').classes('text-gray-400')
                        return

                    with bookings_container:
                        for b in bookings:
                            b_id, s_type, dt, notes, status, worker = b
                            color = 'green' if status == 'Accepted' else ('orange' if status == 'Pending' else 'blue')
                            
                            with ui.card().classes('w-full p-3 bg-slate-50 border border-slate-200'):
                                with ui.row().classes('w-full justify-between items-center'):
                                    ui.label(f'Category: {s_type}').classes('font-bold text-base')
                                    ui.badge(status, color=color)
                                
                                ui.label(f'Schedule: {dt}').classes('text-sm text-gray-700')
                                ui.label(f'Notes: {notes}').classes('text-sm text-gray-600')
                                
                                assigned_text = f'Assigned Caregiver: @{worker}' if worker else 'Waiting for caregiver to accept...'
                                ui.label(assigned_text).classes('text-xs font-bold text-blue-600 mt-1')

                refresh_bookings()


@ui.page('/worker')
def worker_dashboard():
    if not session.user or session.role != 'worker':
        ui.navigate.to('/')
        return

    render_sidebar(f'Worker Portal ({session.specialty})')

    with ui.column().classes('w-full p-6'):
        ui.label(f'{session.specialty} Job Board').classes('text-2xl font-bold mb-4')
        
        jobs_container = ui.column().classes('w-full gap-4')

        def refresh_jobs():
            jobs_container.clear()
            jobs = db.fetch_worker_jobs(session.specialty, session.user)

            if not jobs:
                with jobs_container:
                    ui.label(f'No available or active requests for {session.specialty}.').classes('text-gray-400')
                return

            with jobs_container:
                for j in jobs:
                    b_id, client, dt, notes, status = j
                    color = 'green' if status == 'Accepted' else 'orange'

                    with ui.card().classes('w-full p-4 bg-slate-50 border border-slate-200'):
                        with ui.row().classes('w-full justify-between items-center'):
                            ui.label(f'Client: @{client}').classes('font-bold text-base')
                            ui.badge(status, color=color)

                        ui.label(f'Time Schedule: {dt}').classes('text-sm text-gray-700')
                        ui.label(f'Details: {notes}').classes('text-sm text-gray-600')

                        with ui.row().classes('w-full justify-end mt-2'):
                            if status == 'Pending':
                                def accept_job(job_id=b_id):
                                    db.update_job_status(job_id, session.user, 'Accepted')
                                    ui.notify('Job Accepted!', type='positive')
                                    refresh_jobs()
                                ui.button('Accept Job', on_click=accept_job).props('small').classes('bg-green-600 text-white')
                            
                            elif status == 'Accepted':
                                def complete_job(job_id=b_id):
                                    db.update_job_status(job_id, session.user, 'Completed')
                                    ui.notify('Job Completed!', type='positive')
                                    refresh_jobs()
                                ui.button('Mark Completed', on_click=complete_job).props('small').classes('bg-blue-600 text-white')

        refresh_jobs()


# --- SAFE MAIN GUARD FOR MULTIPROCESSING ---
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        native=True,              # Native desktop window mode
        window_size=(1100, 720),  # Desktop window dimensions
        fullscreen=False,
        reload=False,             # Required False for native desktop apps
        title="CareConnect Desktop"
    )