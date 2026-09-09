from datetime import date
from pathlib import Path
import database as db
from nicegui import app, ui

db.init_db()


class State:

    def __init__(self):
        self.user = None
        self.role = None
        self.fullname = None
        self.specialty = None


session = State()

# Pricing models mapped to durations
PLAN_PRICING = {
    "3 Months Plan": 199.00,
    "6 Months Plan": 349.00,
    "1 Year Plan": 599.00,
}

TIME_SLOTS = [
    f"{hour:02d}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
    for hour in range(6, 22)
    for minute in (0, 30)
]

BASE_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = BASE_DIR / "resources"
RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
app.add_static_files("/resources", str(RESOURCES_DIR))


# --- AUTH UI ---
@ui.page("/")
def login_page():
    session.user = None

    with ui.card().classes(
        "w-96 absolute-center p-6 shadow-2xl rounded-xl bg-white"
    ):
        ui.label("GharSaathi Care Service").classes(
            "text-2xl font-bold text-slate-800 text-center w-full"
        )
        ui.label("Caregiver & Subscription Portal").classes(
            "text-xs text-gray-500 text-center w-full mb-4"
        )

        with ui.tabs().classes("w-full") as tabs:
            login_tab = ui.tab("Login")
            register_tab = ui.tab("Register")

        with ui.tab_panels(tabs, value=login_tab).classes("w-full mt-2"):
            with ui.tab_panel(login_tab):
                username_input = ui.input("Username").classes("w-full")
                password_input = ui.input(
                    "Password", password=True, password_toggle_button=True
                ).classes("w-full")

                def handle_login():
                    u = username_input.value.strip()
                    p = password_input.value.strip()
                    res = db.authenticate_user(u, p)
                    if res:
                        session.user = u
                        session.role, session.specialty, session.fullname = res
                        ui.navigate.to(
                            "/client" if session.role == "user" else "/worker"
                        )
                    else:
                        ui.notify("Invalid Credentials", type="negative")

                ui.button("Login", on_click=handle_login).classes(
                    "w-full mt-4 bg-indigo-600 text-white"
                )

            with ui.tab_panel(register_tab):
                reg_fullname = ui.input("Full Name").classes("w-full")
                reg_username = ui.input("Username").classes("w-full")
                reg_password = ui.input("Password", password=True).classes(
                    "w-full"
                )
                role_select = ui.select(
                    {"user": "Client / Family", "worker": "Caregiver Worker"},
                    value="user",
                    label="Role",
                ).classes("w-full")
                specialty_select = ui.select(
                    ["Babysitting", "Elderly Care", "Pet Care"],
                    value="Babysitting",
                    label="Specialty",
                ).classes("w-full")
                specialty_select.bind_visibility_from(
                    role_select, "value", value="worker"
                )

                def handle_register():
                    fn, u, p = (
                        reg_fullname.value.strip(),
                        reg_username.value.strip(),
                        reg_password.value.strip(),
                    )
                    r, s = (
                        role_select.value,
                        (
                            specialty_select.value
                            if role_select.value == "worker"
                            else None
                        ),
                    )
                    if not fn or not u or not p:
                        ui.notify("Please fill all fields", type="warning")
                        return
                    success, msg = db.register_user(u, p, fn, r, s)
                    if success:
                        ui.notify(msg, type="positive")
                        tabs.set_value(login_tab)
                    else:
                        ui.notify(msg, type="negative")

                ui.button("Register Account", on_click=handle_register).classes(
                    "w-full mt-4 bg-emerald-600 text-white"
                )


def render_sidebar(role_title):
    with ui.left_drawer(value=True).classes("bg-slate-900 text-white p-4 w-64"):
        ui.label("GharSaathi").classes("text-2xl font-bold text-emerald-400")
        ui.label(role_title).classes("text-xs text-gray-400 mb-6")

        with ui.card().classes(
            "bg-slate-800 p-3 text-white w-full mb-6 border border-slate-700"
        ):
            ui.label(session.fullname or "User").classes("font-bold text-sm")
            ui.label(f"@{session.user}").classes("text-xs text-gray-400")

        ui.element("div").classes("flex-grow")
        ui.button(
            "Logout", color="negative", on_click=lambda: ui.navigate.to("/")
        ).classes("w-full")


# --- CLIENT PORTAL ---
@ui.page("/client")
def client_dashboard():
    if not session.user or session.role != "user":
        ui.navigate.to("/")
        return

    selected_reqs = set()
    render_sidebar("Client Subscription Portal")

    with ui.column().classes("w-full p-6 bg-slate-50 min-h-screen"):
        ui.label("Client Dashboard & Subscriptions").classes(
            "text-2xl font-bold text-slate-800 mb-4"
        )

        with ui.row().classes("w-full gap-6 items-start"):
            # Left: Subscription Form
            with ui.card().classes("w-96 p-5 shadow-lg rounded-lg bg-white"):
                ui.label("Book & Subscribe").classes(
                    "text-lg font-bold text-slate-700 mb-2"
                )

                service_opt = ui.select(
                    ["Babysitting", "Elderly Care", "Pet Care"],
                    value="Babysitting",
                    label="Category",
                ).classes("w-full")
                duration_opt = ui.select(
                    list(PLAN_PRICING.keys()),
                    value="3 Months Plan",
                    label="Subscription Duration",
                ).classes("w-full")

                price_lbl = ui.label().classes(
                    "text-sm font-bold text-emerald-600 my-1"
                )

                def update_price_label():
                    price_lbl.set_text(
                        f"Total Billing: ${PLAN_PRICING[duration_opt.value]:.2f}"
                    )

                duration_opt.on("value-change", update_price_label)
                update_price_label()

                ui.label("Service Start Date").classes(
                    "text-xs font-semibold text-gray-600 mt-2"
                )
                with ui.input("Booking Date", value=str(date.today())).classes(
                    "w-full mb-2"
                ) as date_input:
                    with ui.menu() as menu:
                        ui.date().bind_value(date_input).on(
                            "value-change", menu.close
                        )
                    with date_input.add_slot("append"):
                        ui.icon("edit_calendar").on(
                            "click", menu.open
                        ).classes("cursor-pointer")

                ui.label("Time Slot Window").classes(
                    "text-xs font-semibold text-gray-600 mt-2"
                )
                with ui.row().classes("w-full gap-2 items-center mb-2"):
                    from_time_select = ui.select(
                        options=TIME_SLOTS, value=TIME_SLOTS[4], label="From"
                    ).classes("w-1/2")
                    till_time_select = ui.select(
                        options=TIME_SLOTS, value=TIME_SLOTS[12], label="Till"
                    ).classes("w-1/2")

                # Requirements Chips Setup
                ui.label("Custom Requirements").classes(
                    "text-xs font-semibold text-gray-600 mt-2"
                )
                with ui.row().classes("w-full gap-2 items-center mb-2"):
                    custom_req_input = ui.input(
                        placeholder="E.g., Pet walking, Medication"
                    ).classes("flex-grow")

                    def add_req():
                        val = custom_req_input.value.strip()
                        if val and val not in selected_reqs:
                            selected_reqs.add(val)
                            custom_req_input.value = ""
                            render_chips()

                    ui.button("Add", on_click=add_req).classes(
                        "bg-slate-700 text-white"
                    )

                chips_container = ui.row().classes(
                    "w-full gap-1 mb-4 p-2 bg-slate-100 rounded-lg border min-h-[40px]"
                )

                def render_chips():
                    chips_container.clear()
                    with chips_container:
                        for req in list(selected_reqs):

                            def remove(r=req):
                                selected_reqs.remove(r)
                                render_chips()

                            with ui.row().classes(
                                "bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full items-center text-xs"
                            ):
                                ui.label(req)
                                ui.button("×", on_click=remove).props(
                                    "flat round dense"
                                ).classes("text-xs ml-1 font-bold")

                render_chips()

                # Payment Modal Setup
                payment_dialog = ui.dialog()
                with payment_dialog, ui.card().classes("w-96 p-5"):
                    ui.label("Complete Checkout").classes(
                        "text-lg font-bold mb-2"
                    )
                    payment_type = ui.radio(
                        ["Credit Card", "QR Code (UPI)"], value="Credit Card"
                    ).classes("mb-2")

                    card_container = ui.column().classes("w-full")
                    with card_container:
                        card_num = ui.input(
                            "Card Number", placeholder="4532 8890 1234 5678"
                        ).classes("w-full")
                        with ui.row().classes("w-full"):
                            card_exp = ui.input(
                                "MM/YY", placeholder="12/28"
                            ).classes("w-1/2")
                            card_cvv = ui.input(
                                "CVV", password=True, placeholder="123"
                            ).classes("w-1/2")

                    qr_container = ui.column().classes("w-full items-center hidden")
                    with qr_container:
                        ui.label("Scan Dummy UPI Code").classes(
                            "text-xs text-gray-500 mb-2"
                        )
                        with ui.element("div").classes(
                            "w-40 h-40 bg-black p-2 grid grid-cols-4 gap-1 rounded"
                        ):
                            for _ in range(16):
                                ui.element("div").classes("bg-white rounded-sm")

                    def toggle_pay_method():
                        if payment_type.value == "Credit Card":
                            card_container.classes(remove="hidden")
                            qr_container.classes(add="hidden")
                        else:
                            card_container.classes(add="hidden")
                            qr_container.classes(remove="hidden")

                    payment_type.on("value-change", toggle_pay_method)

                    def confirm_payment():
                        method = (
                            f"Card (*{card_num.value[-4:]})"
                            if payment_type.value == "Credit Card"
                            else "UPI QR"
                        )
                        notes_str = (
                            ", ".join(selected_reqs)
                            if selected_reqs
                            else "None"
                        )
                        amt = PLAN_PRICING[duration_opt.value]

                        db.create_booking(
                            session.user,
                            service_opt.value,
                            date_input.value,
                            from_time_select.value,
                            till_time_select.value,
                            duration_opt.value,
                            amt,
                            notes_str,
                            method,
                        )
                        ui.notify(
                            "Subscription Activated & Payment Processed!",
                            type="positive",
                        )
                        payment_dialog.close()
                        selected_reqs.clear()
                        render_chips()
                        refresh_bookings()

                    ui.button(
                        "Pay & Subscribe", on_click=confirm_payment
                    ).classes("w-full mt-4 bg-emerald-600 text-white")

                ui.button(
                    "Proceed to Payment", on_click=payment_dialog.open
                ).classes("w-full bg-indigo-600 text-white")

            # Right: Active Subscriptions
            with ui.card().classes("flex-1 p-5 shadow-lg rounded-lg bg-white"):
                ui.label("My Active Care Subscriptions").classes(
                    "text-lg font-bold text-slate-800 mb-4"
                )
                bookings_container = ui.column().classes("w-full gap-3")

                def refresh_bookings():
                    bookings_container.clear()
                    bookings = db.fetch_client_bookings(session.user)
                    if not bookings:
                        with bookings_container:
                            ui.label("No active subscriptions found.").classes(
                                "text-gray-400"
                            )
                        return

                    with bookings_container:
                        for b in bookings:
                            (
                                b_id,
                                s_type,
                                dt,
                                dur,
                                amt,
                                notes,
                                status,
                                worker,
                                pay_m,
                            ) = b
                            status_color = (
                                "emerald"
                                if status == "Accepted"
                                else ("amber" if status == "Pending" else "blue")
                            )

                            with ui.card().classes(
                                "w-full p-4 bg-slate-50 border border-slate-200 rounded-md"
                            ):
                                with ui.row().classes(
                                    "w-full justify-between items-center"
                                ):
                                    ui.label(f"{s_type} ({dur})").classes(
                                        "font-bold text-base text-slate-800"
                                    )
                                    ui.badge(status, color=status_color)

                                ui.label(f"Schedule: {dt}").classes(
                                    "text-xs text-gray-600"
                                )
                                ui.label(
                                    f"Paid: ${amt:.2f} via {pay_m}"
                                ).classes("text-xs text-emerald-700 font-bold")
                                ui.label(f"Requirements: {notes}").classes(
                                    "text-xs text-gray-500"
                                )

                                assigned = (
                                    f"Assigned Caregiver: @{worker}"
                                    if worker
                                    else "Searching for qualified caregiver..."
                                )
                                ui.label(assigned).classes(
                                    "text-xs font-semibold text-indigo-600 mt-2"
                                )

                refresh_bookings()


# --- WORKER / CAREGIVER PORTAL ---
@ui.page("/worker")
def worker_dashboard():
    if not session.user or session.role != "worker":
        ui.navigate.to("/")
        return

    render_sidebar(f"Caregiver Portal ({session.specialty})")

    with ui.column().classes("w-full p-6 bg-slate-50 min-h-screen"):
        # Financial Overview Metrics
        total_payout = db.fetch_worker_earnings(session.user)
        with ui.row().classes("w-full mb-6 gap-4"):
            with ui.card().classes(
                "p-4 bg-white border border-slate-200 shadow-sm rounded-lg flex-1"
            ):
                ui.label("Total Earned Payout (70%)").classes(
                    "text-xs text-gray-500 font-bold uppercase"
                )
                ui.label(f"${total_payout:.2f}").classes(
                    "text-3xl font-extrabold text-emerald-600"
                )
            with ui.card().classes(
                "p-4 bg-white border border-slate-200 shadow-sm rounded-lg flex-1"
            ):
                ui.label("Platform Split Standard").classes(
                    "text-xs text-gray-500 font-bold uppercase"
                )
                ui.label("70% Worker / 30% Platform").classes(
                    "text-base font-bold text-slate-700 mt-2"
                )

        ui.label(f"Available Jobs: {session.specialty}").classes(
            "text-xl font-bold text-slate-800 mb-2"
        )
        jobs_container = ui.column().classes("w-full gap-4")

        def refresh_jobs():
            jobs_container.clear()
            jobs = db.fetch_worker_jobs(session.specialty, session.user)

            if not jobs:
                with jobs_container:
                    ui.label(
                        f"No open requests in {session.specialty}."
                    ).classes("text-gray-400")
                return

            with jobs_container:
                for j in jobs:
                    b_id, client, dt, dur, payout, notes, status = j
                    badge_color = "emerald" if status == "Accepted" else "amber"

                    with ui.card().classes(
                        "w-full p-4 bg-white border border-slate-200 shadow-sm rounded-md"
                    ):
                        with ui.row().classes(
                            "w-full justify-between items-center"
                        ):
                            ui.label(f"Client Request: @{client}").classes(
                                "font-bold text-slate-800"
                            )
                            ui.badge(status, color=badge_color)

                        ui.label(f"Contract Term: {dur} ({dt})").classes(
                            "text-xs text-gray-600"
                        )
                        ui.label(f"Care Requirements: {notes}").classes(
                            "text-xs text-gray-500"
                        )
                        ui.label(
                            f"Net Caregiver Payout (70%): ${payout:.2f}"
                        ).classes("text-sm font-bold text-emerald-600 mt-1")

                        with ui.row().classes("w-full justify-end mt-2"):
                            if status == "Pending":

                                def accept_job(job_id=b_id):
                                    db.update_job_status(
                                        job_id, session.user, "Accepted"
                                    )
                                    ui.notify("Job Accepted", type="positive")
                                    refresh_jobs()

                                ui.button(
                                    "Accept Contract", on_click=accept_job
                                ).classes("bg-emerald-600 text-white text-xs")

                            elif status == "Accepted":

                                def complete_job(job_id=b_id):
                                    db.update_job_status(
                                        job_id, session.user, "Completed"
                                    )
                                    ui.notify(
                                        "Contract Completed & Payout Credited!",
                                        type="positive",
                                    )
                                    refresh_jobs()

                                ui.button(
                                    "Mark Completed", on_click=complete_job
                                ).classes("bg-indigo-600 text-white text-xs")

        refresh_jobs()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        native=True,
        window_size=(1180, 780),
        fullscreen=False,
        reload=False,
        title="GharSaathi Desktop Caregiver Portal",
    )