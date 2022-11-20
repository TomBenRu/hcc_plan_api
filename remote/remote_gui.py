import datetime
import json
import time
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk

import requests
import tkcalendar
from pydantic import EmailStr

import databases.pydantic_models as pm
from remote.tools import PlaceholderEntry

local = True

# wenn die lokale Datenbank oder die Serverdatenbank von der lokalen API as verwendet wird:
if local:  # or (not local and from_outside):
    SERVER_ADDRESS = 'http://127.0.0.1:8000'
else:
    SERVER_ADDRESS = 'http://hcc-plan-curr.onrender.com'


class MainFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.host: str | None = None

        self.access_token: str | None = None
        self.project: pm.Project | None = None
        self.all_actors: list[dict[str, str]] | None = None
        self.avail_days = {}
        self.planperiod = None

        self.frame_title = ttk.Frame(self, padding='20 20 20 00')
        self.frame_title.pack(fill='x', expand=True)
        self.frame_log = ttk.Frame(self, padding='20 20 20 20')
        self.frame_log.pack(fill='x', expand=True)

        self.lb_title = tk.Label(self.frame_title, text='Verlauf:', justify='left', font=30,)
        self.lb_title.grid()

        self.text_log = tk.Text(self.frame_log, width=90, height=30, bg='#afe0ff')
        self.text_log.grid()

        self.get_host()
        self.login()

    def get_host(self):
        while not self.host:
            try:
                with open('settings_data.json', 'r') as f:
                    settings_data = json.load(f)
                    self.host = settings_data['host']
            except Exception as e:
                tk.messagebox.showinfo(parent=self, message=f'{e}')
                self.settings()
                self.wait_window(self.settings_window)

    def settings(self):
        self.settings_window = Settings(self)

    def new_project(self):
        self.text_log.insert('end', '- new Project\n')
        create_new_project = CreateNewProject(self)
        self.wait_window(create_new_project)
        self.text_log.insert('end', f'-- {self.new_project}')

    def new_person(self):
        self.text_log.insert('end', '- new person\n')

    def new_admin(self):
        self.text_log.insert('end', '- new admin\n')

    def new_dispatcher(self):
        self.text_log.insert('end', '- new dispatcher\n')

    def new_team(self):
        self.text_log.insert('end', '- new team\n')
        CreateTeam(self, self.host)

    def new_actor(self):
        self.text_log.insert('end', '- new actor\n')

    def new_planperiod(self):
        self.text_log.insert('end', '- new planperiod\n')
        create_planperiod = CreatePlanperiod(self, self.host)
        self.wait_window(create_planperiod)
        self.text_log.insert('end', f'-- {self.planperiod}\n')

    def get_all_actors(self):
        self.text_log.insert('end', '- get all clowns\n')
        response = requests.get(f'{self.host}/dispatcher/actors', params={'access_token': self.access_token})
        data = response.json()
        if type(data) == dict and data.get('status_code') == 401:
            tk.messagebox.showerror(parent=self, message='Nicht authorisiert!')
            return
        self.text_log.insert('end', f'-- {response.text}\n')
        self.all_actors = data

    def get_avail_days(self):
        self.get_all_actors()
        self.text_log.insert('end', f'- get avail_days\n')
        if not self.all_actors:
            tk.messagebox.showerror(parent=self, message='Sie müssen zuerst alle Clowns importieren.')
            return
        get_av_days = GetAvailDays(self, self.host)
        self.wait_window(get_av_days)

        self.text_log.insert('end', f'-- {self.avail_days}\n')

    def login(self):
        self.text_log.insert('end', '- login\n')

        LoginWindow(self, self.host)


class CommonTopLevel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.grab_set()
        self.focus_set()
        self.bind('<Escape>', lambda e: self.destroy())

        self.parent = parent


class Settings(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.grab_set()
        self.focus_set()
        self.bind('<Escape>', lambda e: self.destroy())

        self.parent = parent

        self.frame_main = ttk.Frame(self, padding='20 20 20 20')
        self.frame_main.pack()

        self.lb_entry_host = tk.Label(self.frame_main, text='Hostadresse:')
        self.lb_entry_host.grid(row=0, column=0, padx=(0, 5), pady=(0, 5), sticky='w')
        self.entry_host = tk.Entry(self.frame_main)
        self.entry_host.grid(row=0, column=1, padx=(5, 0), pady=(0, 5))

        self.var_chk_save_settings_data = tk.BooleanVar(value=True)
        self.chk_save_settings_data = tk.Checkbutton(self.frame_main, text='Zugangsdaten speichern?',
                                                     variable=self.var_chk_save_settings_data)
        self.chk_save_settings_data.grid(row=3, column=0, columnspan=2, pady=(5, 10))

        self.bt_ok = tk.Button(self.frame_main, text='okay', width=15, command=self.save_settings)
        self.bt_ok.grid(row=4, column=0, padx=(0, 5), pady=(5, 0), sticky='e')
        self.bt_cancel = tk.Button(self.frame_main, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=4, column=1, padx=(5, 0), pady=(5, 0), sticky='w')

    def autofill(self):
        try:
            with open('settings_data.json', 'r') as f:
                settings_data = json.load(f)
        except Exception as e:
            print(e)
            return
        host = settings_data.get('host', '')
        self.entry_host.insert(0, host)

    def save_settings(self):
        if self.var_chk_save_settings_data.get():
            with open('settings_data.json', 'w') as f:
                json.dump({'host': self.entry_host.get()}, f)
        self.parent.host = self.entry_host.get()
        tk.messagebox.showinfo(parent=self, message='Die Einstellungen wurden vorgenommen.')
        self.destroy()


class LoginWindow(tk.Toplevel):
    def __init__(self, parent, host):
        super().__init__(parent)
        self.grab_set()
        self.lift(parent)
        self.focus_set()
        self.bind('<Escape>', lambda event: self.destroy())
        self.bind('<Return>', lambda event: self.save_token())

        self.parent = parent
        self.host = host
        self.access_data: dict[str, dict[str, str]] | None = None

        self.frame_manager = ttk.Frame(self, padding='20 20 20 05')
        self.frame_manager.pack()

        self.frame_mail_psw = ttk.Frame(self, padding='20 05 20 05')
        self.frame_mail_psw.pack()

        self.frame_buttons = ttk.Frame(self, padding='20 05 20 20')
        self.frame_buttons.pack()

        self.var_combo_manager = tk.StringVar(value='Dispatcher')
        self.lb_combo_manager = tk.Label(self.frame_manager, text='Einloggen als...')
        self.lb_combo_manager.grid(row=0, column=0, padx=(0, 5), sticky='e')
        self.combo_manager = ttk.Combobox(self.frame_manager, values=['Supervisor', 'Admin', 'Dispatcher'],
                                          textvariable=self.var_combo_manager, state='readonly')
        self.combo_manager.bind("<<ComboboxSelected>>", lambda event: self.autofill())
        self.combo_manager.grid(row=0, column=1, padx=(5, 0), sticky='w')

        self.lb_entry_email = tk.Label(self.frame_mail_psw, text='Email')
        self.lb_entry_email.grid(row=0, column=0, padx=(0, 5), pady=(0, 5), sticky='w')
        self.entry_email = tk.Entry(self.frame_mail_psw)
        self.entry_email.grid(row=0, column=1, padx=(5, 0), pady=(0, 5))
        self.lb_entry_password = tk.Label(self.frame_mail_psw, text='Password')
        self.lb_entry_password.grid(row=1, column=0, padx=(0, 5), pady=(5, 5), sticky='w')
        self.entry_password = tk.Entry(self.frame_mail_psw, show='*')
        self.entry_password.grid(row=1, column=1, padx=(5, 0), pady=(5, 5))

        self.var_chk_save_access_data = tk.BooleanVar(value=False)
        self.chk_save_access_data = tk.Checkbutton(self.frame_mail_psw, text='Zugangsdaten speichern?',
                                                   variable=self.var_chk_save_access_data)
        self.chk_save_access_data.grid(row=3, column=0, columnspan=2, pady=(5, 0))

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=15, command=self.save_token)
        self.bt_ok.grid(row=0, column=0, padx=(0, 5), pady=(0, 0), sticky='e')
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, padx=(5, 0), pady=(0, 0), sticky='w')

        self.autofill()

    def autofill(self):
        try:
            with open('access_data.json', 'r') as f:
                self.access_data = json.load(f)
        except Exception as e:
            print(e)
            self.entry_email.delete(0, 'end')
            self.entry_password.delete(0, 'end')
            return
        if not self.access_data.get(self.var_combo_manager.get()):
            self.entry_email.delete(0, 'end')
            self.entry_password.delete(0, 'end')
            return
        self.entry_email.delete(0, 'end')
        self.entry_email.insert(0, self.access_data[self.var_combo_manager.get()]['email'])
        self.entry_password.delete(0, 'end')
        self.entry_password.insert(0, self.access_data[self.var_combo_manager.get()]['password'])

    def save_token(self):
        connection_error = None
        t0 = time.time()
        email = (self.entry_email.get()).lower()
        password = self.entry_password.get()
        while time.time() - t0 < 30:
            try:
                manager = self.var_combo_manager.get()
                prefix = 'su' if manager == 'Supervisor' else 'admin' if manager == 'Admin' else 'dispatcher' if manager == 'Dispatcher' else None
                response = requests.get(f'{self.host}/{prefix}/login',
                                        params={'email': email, 'password': password})

                self.parent.access_token = response.json()['access_token']
                if self.var_chk_save_access_data.get():
                    with open('access_data.json', 'w') as f:
                        if not self.access_data:
                            self.access_data = {}
                        if not self.access_data.get(self.var_combo_manager.get()):
                            self.access_data[self.var_combo_manager.get()] = {}
                        self.access_data[self.var_combo_manager.get()]['email'] = self.entry_email.get()
                        self.access_data[self.var_combo_manager.get()]['password'] = self.entry_password.get()
                        json.dump(self.access_data, f)
                if manager in ('Admin', 'Dispatcher'):
                    self.get_project(prefix)
                self.destroy()
                tk.messagebox.showinfo(parent=self.parent, message='Sie sind erfolgreich eingeloggt.')
                return
            except ConnectionError as e:
                connection_error = e
                time.sleep(0.2)
        raise connection_error

    def get_project(self, prefix: str):
        response = requests.get(f'{self.host}/{prefix}/project',
                                params={'access_token': self.parent.access_token})
        self.parent.project = pm.Project(**response.json())


class CreateNewProject(CommonTopLevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.frame_input = ttk.Frame(self, padding='20 20 20 20')
        self.frame_input.pack()
        self.frame_buttons = ttk.Frame(self, padding='20 20 20 20')
        self.frame_buttons.pack()

        self.lb_entry_projectname = tk.Label(self.frame_input, text='Projektname:')
        self.lb_entry_projectname.grid(row=0, column=0, sticky='e', padx=(0, 5), pady=(0, 10))
        self.entry_projectname = tk.Entry(self.frame_input, width=50)
        self.entry_projectname.grid(row=0, column=1, sticky='w', padx=(5, 0), pady=(0, 10))

        self.lb_entry_fname_admin = tk.Label(self.frame_input, text='Vorname Admin:')
        self.lb_entry_fname_admin.grid(row=1, column=0, sticky='e', padx=(0, 5), pady=(10, 5))
        self.entry_fname_admin = tk.Entry(self.frame_input, width=50)
        self.entry_fname_admin.grid(row=1, column=1, sticky='w', padx=(5, 0), pady=(10, 5))

        self.lb_entry_lname_admin = tk.Label(self.frame_input, text='Nachname Admin:')
        self.lb_entry_lname_admin.grid(row=2, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
        self.entry_lname_admin = tk.Entry(self.frame_input, width=50)
        self.entry_lname_admin.grid(row=2, column=1, sticky='w', padx=(5, 0), pady=(5, 5))

        self.lb_entry_email_admin = tk.Label(self.frame_input, text='Email Admin:')
        self.lb_entry_email_admin.grid(row=3, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
        self.entry_email_admin = tk.Entry(self.frame_input, width=50)
        self.entry_email_admin.grid(row=3, column=1, sticky='w', padx=(5, 0), pady=(5, 5))

        self.lb_entry_password_admin = tk.Label(self.frame_input, text='Passwort Admin:')
        self.lb_entry_password_admin.grid(row=4, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
        self.entry_password_admin = PlaceholderEntry(master=self.frame_input, width=50, show='*',
                                                     placeholder='Wenn leer: Random Passwort wird erzeugt.')
        self.entry_password_admin.grid(row=4, column=1, sticky='w', padx=(5, 0), pady=(5, 5))

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=20, command=self.new_project)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 10))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=20, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(10, 0))

    def new_project(self):
        person = pm.PersonCreate(f_name=self.entry_fname_admin.get(), l_name=self.entry_lname_admin.get(),
                                 email=EmailStr(self.entry_email_admin.get()), password=self.entry_password_admin.get())
        project = pm.ProjectCreate(name=self.entry_projectname.get())
        access_token = pm.Token(access_token=self.parent.access_token, token_type='bearer')
        response = requests.post(f'{self.parent.host}/su/account',
                                 json={'person': person.dict(), 'project': project.dict(),
                                       'access_token': access_token.dict()})
        self.parent.new_project = response.json()
        self.destroy()



class GetAvailDays(tk.Toplevel):
    def __init__(self, parent, host: str):
        super().__init__(parent)
        self.grab_set()
        self.focus_set()
        self.bind('<Escape>', lambda e: self.destroy())

        self.parent = parent
        self.host = host

        self.frame_main = ttk.Frame(self, padding='20 20 20 20')
        self.frame_main.pack()
        self.all_actors = {f'{a["f_name"]}, {a["l_name"]}': a['id'] for a in self.parent.all_actors}
        self.all_actors['allen Clowns'] = '-1'
        self.lb_combo_all_actors = tk.Label(self.frame_main, text='Spieloptionen von...')
        self.lb_combo_all_actors.grid(row=0, column=0, padx=(0, 5))
        self.var_combo_all_actors = tk.StringVar(value='allen Clowns')
        self.combo_all_actors = ttk.Combobox(self.frame_main, values=list(self.all_actors.keys()),
                                             textvariable=self.var_combo_all_actors)
        self.combo_all_actors.grid(row=0, column=1, padx=(5, 0))

        self.bt_ok = tk.Button(self.frame_main, text='okay', width=15, command=self.save_avail_days)
        self.bt_ok.grid(row=1, column=0, padx=(0, 5), pady=(10, 0))
        self.bt_cancel = tk.Button(self.frame_main, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=1, column=1, padx=(5, 0), pady=(10, 0))

    def save_avail_days(self):
        connection_error = None
        t0 = time.time()
        actor_ids = (list(self.all_actors.values())[:-1] if self.all_actors.get(self.var_combo_all_actors.get()) == '-1'
                     else [self.all_actors[self.var_combo_all_actors.get()]])
        while time.time() - t0 < 30:
            try:
                available_days = {}
                for actor_id in actor_ids:
                    response = requests.get(f'{self.host}/dispatcher/avail_days',
                                            params={'access_token': self.parent.access_token, 'actor_id': actor_id})
                    data = response.json()
                    if type(data) == dict and data.get('status_code') == 401:
                        tk.messagebox.showerror(parent=self, message='Nicht authorisiert!')
                        self.destroy()
                    available_days[actor_id] = response.json()
                self.parent.avail_days = available_days

                tk.messagebox.showinfo(parent=self, message='avail_days downloaded.')
                self.destroy()
                return
            except ConnectionError as e:
                connection_error = e
                time.sleep(0.2)
        raise connection_error


class CreateTeam(tk.Toplevel):
    def __init__(self, parent, host: str):
        super().__init__(parent)
        self.grab_set()
        self.focus_set()
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Return>', lambda event: self.save())

        self.parent = parent
        self.host = host

        self.frame_choose_team = ttk.Frame(self, padding='20 20 20 05')
        self.frame_choose_team.pack(fill='x', expand=True)
        self.frame_choose_dispatcher = ttk.Frame(self, padding='20 05 20 20')
        self.frame_choose_dispatcher.pack(fill='x', expand=True)

        self.values_combo_teams = {f'{t.name} (Disp.:{t.dispatcher.person.f_name} {t.dispatcher.person.l_name})': t
                                   for t in self.get_teams()}
        self.values_combo_teams |= {'Team neu anlegen': '-1'}
        self.lb_combo_teams = tk.Label(self.frame_choose_team, text='Team wählen...')
        self.lb_combo_teams.grid(row=0, column=0, padx=(35, 5), sticky='e')
        self.var_combo_teams = tk.StringVar(value=list(self.values_combo_teams.keys())[0])
        self.combo_all_teams = ttk.Combobox(self.frame_choose_team, values=list(self.values_combo_teams.keys()),
                                            textvariable=self.var_combo_teams, state='readonly', width=40)
        self.combo_all_teams.bind('<<ComboboxSelected>>', lambda event: self.new_team())
        self.combo_all_teams.grid(row=0, column=1, padx=(5, 0), sticky='e')

        self.values_combo_persons = {f'{p.f_name} {p.l_name}': p.id for p in self.get_persons()}
        self.values_combo_persons |= {'Person neu anlegen': '-1'}
        self.lb_combo_persons = tk.Label(self.frame_choose_dispatcher, text='Dispatcher für Team...')
        self.lb_combo_persons.grid(row=0, column=0, padx=(0, 5), sticky='e')
        self.var_combo_persons = tk.StringVar(value=list(self.values_combo_persons.keys())[0])
        self.combo_all_persons = ttk.Combobox(self.frame_choose_dispatcher, values=list(self.values_combo_persons.keys()),
                                              textvariable=self.var_combo_persons, state='readonly', width=40)
        self.combo_all_persons.bind('<<ComboboxSelected>>', lambda event: self.new_person())
        self.combo_all_persons.grid(row=0, column=1, padx=(5, 0), sticky='e')

        if self.values_combo_teams.get(self.var_combo_teams.get()) == '-1':
            self.new_team()

    def save(self):
        pass



    def get_persons(self):
        response = requests.get(f'{self.host}/admin/persons', params={'access_token': self.parent.access_token})
        data = response.json()
        if type(data) == dict and data.get('status_code') == 401:
            tk.messagebox.showerror(parent=self, message='Nicht authorisiert!')
            self.destroy()
        return sorted((pm.PersonShow(**p) for p in data), key=lambda person: person.f_name)

    def get_teams(self):
        response = requests.get(f'{self.host}/admin/teams', params={'access_token': self.parent.access_token})
        data = response.json()
        if type(data) == dict and data.get('status_code') == 401:
            tk.messagebox.showerror(parent=self, message='Nicht authorisiert!')
            self.destroy()
        return sorted((pm.TeamShow(**t) for t in data), key=lambda team: team.name)

    def new_team(self):
        class NewTeam(tk.Toplevel):
            def __init__(self, parent):
                super().__init__(parent)
                self.grab_set()
                self.focus_set()
                self.bind('<Escape>', lambda event: self.destroy())
                self.bind('<Return>', lambda event: self.save_team())

                self.parent = parent

                self.lb_name = tk.Label(self, text='Teamname:')
                self.lb_name.grid(row=0, column=0, padx=(10, 5), pady=(10, 5))
                self.entry_name = tk.Entry(self, name='xxxx')
                self.entry_name.grid(row=0, column=1, padx=(5, 10), pady=(10, 5))

            def save_team(self):
                self.parent.var_combo_teams.set(self.entry_name.get())
                self.destroy()

        if self.values_combo_teams.get(self.var_combo_teams.get()) == '-1':
            new_team = NewTeam(self)
            self.wait_window(new_team)
        if self.values_combo_persons.get(self.var_combo_persons.get()) == '-1':
            self.new_person()

    def new_person(self):
        class NewPerson(tk.Toplevel):
            def __init__(self, parent):
                super().__init__(parent)
                self.grab_set()
                self.focus_set()
                self.bind('<Escape>', lambda event: self.destroy())
                self.bind('<Return>', lambda event: self.save_person())

                self.parent = parent

                self.lb_fname = tk.Label(self, text='Vorname:')
                self.lb_fname.grid(row=0, column=0, padx=(10, 5), pady=(10, 5))
                self.entry_fname = tk.Entry(self)
                self.entry_fname.grid(row=0, column=1, padx=(5, 10), pady=(5, 5))
                self.lb_lname = tk.Label(self, text='Nachname:')
                self.lb_lname.grid(row=1, column=0, padx=(10, 5), pady=(5, 5))
                self.entry_lname = tk.Entry(self)
                self.entry_lname.grid(row=1, column=1, padx=(5, 10), pady=(5, 5))
                self.lb_email = tk.Label(self, text='Email:')
                self.lb_email.grid(row=2, column=0, padx=(10, 5), pady=(5, 5))
                self.entry_email = tk.Entry(self)
                self.entry_email.grid(row=2, column=1, padx=(5, 10), pady=(5, 10))

            def save_person(self):
                self.parent.var_combo_persons.set(f'{self.entry_fname.get()} {self.entry_lname.get()} {self.entry_email.get()}')
                self.destroy()

        NewPerson(self)


class CreatePlanperiod(tk.Toplevel):
    def __init__(self, parent, host: str):
        super().__init__(parent)
        self.grab_set()
        self.focus_set()
        self.bind('<Escape>', lambda e: self.destroy())

        self.parent = parent
        self.host = host

        self.date = datetime.datetime.now()
        self.teams: list[pm.TeamShow] | None = None
        self.values_combo_teams: dict[str, str] | None = None

        self.frame_team = ttk.Frame(self, padding='20 20 20 20')
        self.frame_team.pack()
        self.frame_calendar = ttk.Frame(self, padding='20 20 20 20')
        self.frame_calendar.pack()
        self.frame_notes = ttk.Frame(self, padding='20 20 20 20')
        self.frame_notes.pack()
        self.frame_buttons = ttk.Frame(self, padding='20 20 20 20')
        self.frame_buttons.pack()

        self.lb_combo_teams = tk.Label(self.frame_team, text='Wählen Sie ein Team:')
        self.lb_combo_teams.grid(row=0, column=0, padx=(0, 5), sticky='e')
        self.var_combo_teams = tk.StringVar()
        self.combo_teams = ttk.Combobox(self.frame_team, textvariable=self.var_combo_teams, state='readonly')
        self.combo_teams.bind('<<ComboboxSelected>>', lambda event: self.get_last_day_of_existing_planperiods())
        self.combo_teams.grid(row=0, column=1, padx=(5, 0), sticky='w')

        self.lb_calendar_from = tk.Label(self.frame_calendar, text='Ersten Tag auswählen:')
        self.lb_calendar_from.grid(row=0, column=0, sticky='w')
        self.calendar_from = tkcalendar.dateentry.DateEntry(self.frame_calendar, locale='de_DE', width=20,
                                                            date_pattern='dd.mm.yyyy')
        self.calendar_from.grid(row=1, column=0, padx=(0, 5), sticky='w')
        self.lb_calendar_to = tk.Label(self.frame_calendar, text='Letzten Tag auswählen:')
        self.lb_calendar_to.grid(row=0, column=1, sticky='w')
        self.calendar_to = tkcalendar.dateentry.DateEntry(self.frame_calendar, locale='de_DE', width=20,
                                                          date_pattern='dd.mm.yyyy')
        self.calendar_to.grid(row=1, column=1, padx=(5, 5), sticky='w')
        self.lb_calendar_notes = tk.Label(self.frame_calendar, text='Termin Deadline:')
        self.lb_calendar_notes.grid(row=0, column=2, sticky='w')
        self.calendar_notes = tkcalendar.dateentry.DateEntry(self.frame_calendar, locale='de_DE', width=20,
                                                             date_pattern='dd.mm.yyyy')
        self.calendar_notes.grid(row=1, column=2, padx=(5, 0), sticky='w')

        self.lb_text_notes = tk.Label(self.frame_notes, text='Notitzen:')
        self.lb_text_notes.grid(row=0, column=0, sticky='w')
        self.text_notes = tk.Text(self.frame_notes, width=50, height=10)
        self.text_notes.grid(row=1, column=0, sticky='w')

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=15, command=self.create_period)
        self.bt_ok.grid(row=0, column=0, padx=(0, 10), sticky='e')
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, padx=(10, 0), sticky='w')

        self.get_teams_and_mindates()

    def get_teams_and_mindates(self):
        response = requests.get(f'{self.host}/dispatcher/teams',
                                params={'access_token': self.parent.access_token})
        data = response.json()
        if type(data) == dict and data.get('status_code') == 401:
            tk.messagebox.showerror(parent=self, message='Nicht authorisiert!')
            self.destroy()
        self.teams = [pm.TeamShow(**team) for team in data]
        self.values_combo_teams = {team.name: team.id for team in self.teams}
        self.var_combo_teams.set(self.teams[0].name)
        self.combo_teams.config(values=list(self.values_combo_teams))

        self.get_last_day_of_existing_planperiods()

    def get_last_day_of_existing_planperiods(self):
        team_id = self.values_combo_teams[self.var_combo_teams.get()]
        response = requests.get(f'{self.host}/dispatcher/pp_last_recent_date',
                                params={'access_token': self.parent.access_token, 'team_id': team_id})
        data = response.json()
        if type(data) == dict and data.get('status_code') == 401:
            tk.messagebox.showerror(parent=self, message='Nicht authorisiert!')
            self.destroy()
        last_day: str = response.json()
        last_day: datetime.date = datetime.date(*[int(v) for v in last_day.split('-')])
        mindate = last_day + datetime.timedelta(days=1)
        self.calendar_from.config(mindate=mindate)
        self.calendar_from.set_date(mindate)
        self.calendar_to.config(mindate=mindate)
        self.calendar_to.set_date(mindate)

    def create_period(self):
        team_id = self.values_combo_teams[self.var_combo_teams.get()]
        start: datetime.date = self.calendar_from.get_date()
        end: datetime.date = self.calendar_to.get_date()
        deadline: datetime.date = self.calendar_notes.get_date()
        notes = self.text_notes.get(1.0, 'end')

        response = requests.post(f'{self.parent.host}/dispatcher/planperiod',
                                 params={'access_token': self.parent.access_token, 'team_id': team_id,
                                         'date_start': start.isoformat(), 'date_end': end.isoformat(),
                                         'deadline': deadline, 'notes': notes})
        self.parent.planperiod = response.json()
        self.destroy()
        tk.messagebox.showinfo(parent=self.parent, message='Planperiode wurde erfolgreich erstellt.')


class MainMenu(tk.Menu):
    def __init__(self, parent, root: tk.Tk):
        super().__init__(master=parent)
        root.config(menu=self)
        self.file = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Datei', underline=0, menu=self.file)

        self.export = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Export', underline=0, menu=self.export)

        self.supervisor = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Supervisor', underline=0, menu=self.supervisor)

        self.fetch_data = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Import', underline=0, menu=self.fetch_data)

        self.new_data = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Neue Einträge', underline=0, menu=self.new_data)

        self.edit_data = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Einträge verändern')

        self.login = tk.Menu(self, tearoff=0)
        self.add_cascade(label='login', underline=0, command=parent.login)

        self.file.add_command(label='Einstellungen', command=parent.settings)

        self.supervisor.add_command(label='Neues Projekt', command=parent.new_project)

        self.new_data.add_command(label='Neues Projekt', command=parent.new_project)
        self.new_data.add_command(label='Neue/r Mitarbeiter:in', command=parent.new_person)
        self.new_data.add_command(label='Neue/r Admin', command=parent.new_admin)
        self.new_data.add_command(label='Neue/r Planer:in', command=parent.new_dispatcher)
        self.new_data.add_command(label='Neues Team', command=parent.new_team)
        self.new_data.add_command(label='Neue/r Clown', command=parent.new_actor)
        self.new_data.add_command(label='Neue Planperiode', command=parent.new_planperiod)

        self.fetch_data.add_command(label='Alle Clowns', command=parent.get_all_actors)
        self.fetch_data.add_command(label='Spieloptionen...', command=parent.get_avail_days)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Datenbankverwaltung')
    root.geometry('800x600+00+00')
    mainframe = MainFrame(root)
    mainframe.pack()
    root.menubar = MainMenu(parent=mainframe, root=root)
    root.mainloop()
