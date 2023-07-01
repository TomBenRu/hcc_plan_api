import datetime
import json
import threading
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from typing import Literal, Optional

import requests
import tkcalendar
import jwt
from pydantic import EmailStr, BaseModel

import databases.pydantic_models as pm
from databases.enums import AuthorizationTypes
from remote.tools import PlaceholderEntry
from remote.progressbars import ProgressIndeterm

local = True

# wenn die lokale Datenbank oder die Serverdatenbank von der lokalen API as verwendet wird:
if local:  # or (not local and from_outside):
    SERVER_ADDRESS = 'http://127.0.0.1:8000'
else:
    SERVER_ADDRESS = 'https://hcc-plan-api.onrender.com'


class MainFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.host: str | None = None
        self.access_token = None
        self.authorizations = []

        self.project: pm.Project | None = None
        self.new_project_data: dict | None = None
        self.new_person_data: dict | None = None
        self.new_team_data: dict | None = None
        self.changed_team: pm.Team | None = None
        self.all_actors: list[dict[str, str]] | None = None
        self.avail_days = {}
        self.planperiod = None
        self.new_jobs = None

        self.frame_title = ttk.Frame(self, padding='20 20 20 00')
        self.frame_title.pack(fill='x', expand=True)
        self.frame_log = ttk.Frame(self, padding='20 20 20 20')
        self.frame_log.pack(fill='x', expand=True)

        self.lb_title = tk.Label(self.frame_title, text='Verlauf:', justify='left', font=30,)
        self.lb_title.grid()

        self.scroll_text_log = tk.Scrollbar(self.frame_log, orient='vertical')
        self.scroll_text_log.pack(side='right', fill='y')
        self.text_log = tk.Text(self.frame_log, width=90, height=30, bg='#afe0ff',
                                yscrollcommand=self.scroll_text_log.set)
        self.text_log.pack(side='left')
        self.scroll_text_log.config(command=self.text_log.yview)

        self.get_host()
        self.login()

    def match_ids(self):
        MakeHashmapToHccDispo(self)

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
        if AuthorizationTypes.supervisor.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Superuser-Rechte.')
            return
        create_new_project = CreateNewProject(self, self.access_token)
        self.wait_window(create_new_project)
        self.text_log.insert('end', f'-- {self.new_project_data}')

    def delete_account(self):
        self.text_log.insert('end', '- delete account\n')
        if AuthorizationTypes.admin.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Admin-Rechte.')
            return
        DeleteAccount(self, self.access_token)

    def new_person(self):
        self.text_log.insert('end', '- new person\n')
        if not AuthorizationTypes.admin.value in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Admin-Rechte.')
            return
        create_person = CreatePerson(self, self.access_token)
        self.wait_window(create_person)
        self.text_log.insert('end', f'-- {self.new_person_data}\n')

    def new_team(self):
        if AuthorizationTypes.admin.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Admin-Rechte.')
            return
        self.text_log.insert('end', '- new team\n')
        create_team = CreateTeam(self, self.access_token)
        self.wait_window(create_team)
        self.text_log.insert('end', f'-- {self.new_team_data}\n')

    def change_team(self):
        if AuthorizationTypes.admin.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Admin-Rechte.')
            return
        self.text_log.insert('end', '- change team\n')
        change_team = ChangeTeam(self, self.access_token)
        self.wait_window(change_team)
        self.text_log.insert('end', f'-- {self.changed_team}\n')

    def delete_team(self):
        if AuthorizationTypes.admin.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Admin-Rechte.')
            return
        self.text_log.insert('end', '- delete team\n')
        DeleteTeam(self, self.access_token)

    def change_person_names(self):
        self.text_log.insert('end', '- change person names\n')
        if AuthorizationTypes.admin.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Admin-Rechte.')
            return
        change_names = ChangePersonNames(self, self.access_token)
        self.wait_window(change_names)
        self.text_log.insert('end', f'-- {self.new_person_data}\n')

    def assign_person_to_position(self):
        self.text_log.insert('end', '- new jobs for persons\n')
        if AuthorizationTypes.admin.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Admin-Rechte.')
            return
        assign_person = AssignPersonToPosition(self, self.access_token)
        self.wait_window(assign_person)
        self.text_log.insert('end', f'-- {self.new_jobs}\n')

    def delete_person(self):
        self.text_log.insert('end', '- delete entry\n')
        if AuthorizationTypes.admin.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Admin-Rechte.')
            return
        DeletePerson(parent=self, access_token=self.access_token)

    def new_planperiod(self):
        if AuthorizationTypes.dispatcher.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Dispatcher-Rechte.')
            return
        self.text_log.insert('end', '- new planperiod\n')
        create_planperiod = CreatePlanperiod(self, self.host, self.access_token)
        self.wait_window(create_planperiod)
        self.text_log.insert('end', f'-- {self.planperiod}\n')

    def delete_planperiod(self):
        if AuthorizationTypes.dispatcher.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Dispatcher-Rechte.')
            return
        self.text_log.insert('end', '- delete planperiod\n')
        DeletePlanperiod(self, self.access_token)

    def change_planperiod(self):
        self.text_log.insert('end', '- change planperiod\n')
        if AuthorizationTypes.dispatcher.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Dispatcher-Rechte.')
            return
        change_planperiod = ChangePlanPeriod(self, self.access_token)
        self.wait_window(change_planperiod)
        self.text_log.insert('end', f'-- {self.planperiod}\n')

    def change_project_name(self):
        self.text_log.insert('end', '- new planperiod\n')
        if AuthorizationTypes.admin.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Admin-Rechte.')
            return
        ChangeProjectName(self, self.access_token)

    def get_all_actors(self):
        self.text_log.insert('end', '- get all clowns\n')
        if AuthorizationTypes.dispatcher.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Dispatcher-Rechte.')
        persons = HelperRequests.get_all_actors(self, self.host, self.access_token)
        persons_clean = '\n'.join([f'Name: {p.f_name} {p.l_name}, Projekt: {p.project.name}, '
                                   f'Team: {p.team_of_actor.name if p.team_of_actor else "kein Team"}, '
                                   f'Dipspatcher: {[t.name for t in p.teams_of_dispatcher]}, '
                                   f'Admin: {p.project_of_admin.name if p.project_of_admin else "kein Admin"}' for p in persons])
        self.text_log.insert('end', f'-- {persons_clean}\n')
        self.all_actors = persons

    def get_avail_days(self):
        if AuthorizationTypes.dispatcher.value not in self.authorizations:
            tk.messagebox.showerror(parent=self, title='Login', message='Sie haben keine Dispatcher-Rechte.')
            return
        self.text_log.insert('end', f'- get avail_days\n')
        get_av_days = GetAvailDays(self, self.host, self.access_token)
        self.wait_window(get_av_days)

        txt_to_insert = ''
        for per_id, avd in self.avail_days.items():
            txt_to_insert += f'{per_id}:\n{avd}\n'
        self.text_log.insert('end', f'-- {txt_to_insert}\n')

    def login(self):
        self.text_log.insert('end', '- login\n')

        Login(self)


class HelperRequests:
    def __init__(self):
        pass

    @classmethod
    def get_all_actors(cls, parent, host: str, access_token: str) -> list[pm.PersonShow]:
        response = requests.get(f'{host}/dispatcher/actors',
                                headers={'Authorization': f'Bearer {access_token}'})
        try:
            persons: list[pm.PersonShow] = [pm.PersonShow.parse_obj(p) for p in response.json()]
            return persons
        except Exception as e:
            tk.messagebox.showerror(parent=parent, message=f'{response.text} Fehler: {e}')

    @classmethod
    def get_teams_dispatcher(cls, parent, host: str, access_token: str):
        response = requests.get(f'{host}/dispatcher/teams',
                                headers={'Authorization': f'Bearer {access_token}'})
        try:
            return sorted([pm.Team(**t) for t in response.json()], key=lambda t: t.name)
        except Exception as e:
            tk.messagebox.showerror(parent=parent, message=f'{response.text} Fehler: {e}')

    @staticmethod
    def get_teams_admin(parent, host: str, access_token):
        response = requests.get(f'{host}/admin/teams',
                                headers={'Authorization': f'Bearer {access_token}'})
        data = response.json()
        try:
            teams = [pm.Team.parse_obj(team) for team in data]
            return teams
        except:
            tk.messagebox.showerror(parent=parent, message=f'{response.text}')

    @classmethod
    def get_planperiods(cls, parent, host: str, access_token: str, team_id: str):
        response = requests.get(f'{host}/dispatcher/planperiods',
                                params={'team_id': team_id},
                                headers={'Authorization': f'Bearer {access_token}'})
        try:
            planperiods = sorted([pm.PlanPeriod(**pp) for pp in response.json()], key=lambda v: v.start, reverse=True)
            return planperiods
        except Exception as e:
            tk.messagebox.showerror(parent=parent, message=f'{response.text} Fehler: {e}')


class CommonTopLevel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.grab_set()
        self.focus_set()
        self.bind('<Escape>', lambda e: self.destroy())

        self.parent = parent

        self.frame_combo_select = ttk.Frame(self)
        self.frame_combo_select.pack()
        self.frame_input = ttk.Frame(self, padding='20 20 20 20')
        self.frame_input.pack()
        self.frame_buttons = ttk.Frame(self, padding='20 20 20 20')
        self.frame_buttons.pack()


class MakeHashmapToHccDispo(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        try:
            with open('match_ids.json', 'r') as f:
                self.match_ids = json.load(f)
        except Exception as e:
            print(e)
            with open('match_ids.json', 'w') as f:
                json.dump({}, f)
            self.match_ids = {}
        with open('dispodaten_blanko__BW.json', 'r') as f:
            dispodaten_bw = json.load(f)
        with open('dispodaten_blanko__Mainz.json', 'r') as f:
            dispodaten_mainz = json.load(f)

        self.frame_combo_choice = ttk.Frame(self, padding='20 20 20 20 ')
        self.frame_combo_choice.pack()
        self.frame_entrys = ttk.Frame(self, padding='20 20 20 20')
        self.frame_entrys.pack()
        self.frame_buttons = ttk.Frame(self, padding='20 20 20 20')
        self.frame_buttons.pack()

        self.dispodaten = {'Baden-Württemberg': dispodaten_bw, 'Mainz': dispodaten_mainz}

        self.var_combo_teams = tk.StringVar()
        self.var_combo_persons = tk.StringVar()
        self.values_combo_teams = list(self.dispodaten)
        self.values_combo_persons = {}

        self.lb_combo_teams = tk.Label(self.frame_combo_choice, text='Auswahl Team')
        self.lb_combo_teams.grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.lb_combo_person = tk.Label(self.frame_combo_choice, text='Auswahl Person')
        self.lb_combo_person.grid(row=0, column=1, sticky='w', padx=(5, 0))
        self.combo_teams = ttk.Combobox(self.frame_combo_choice, values=self.values_combo_teams,
                                        textvariable=self.var_combo_teams)
        self.combo_teams.bind('<<ComboboxSelected>>', lambda event: self.autofill_persons())
        self.combo_teams.grid(row=1, column=0, sticky='w', padx=(0, 5))
        self.combo_persons = ttk.Combobox(self.frame_combo_choice, textvariable=self.var_combo_persons)
        self.combo_persons.grid(row=1, column=1, sticky='w', padx=(5, 0))

        self.lb_uuid = tk.Label(self.frame_entrys, text='Hier UUID eintragen:')
        self.lb_uuid.grid(row=0, column=0, sticky='w')
        self.entry_uuid = tk.Entry(self.frame_entrys, width=30)
        self.entry_uuid.grid(row=1, column=0, sticky='w')

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=15, command=self.save)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_apply = tk.Button(self.frame_buttons, text='apply', width=15, command=self.apply)
        self.bt_apply.grid(row=0, column=1, sticky='ew', padx=(5, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=2, sticky='w', padx=(5, 0))

    def save(self):
        with open('match_ids.json', 'w') as f:
            json.dump(self.match_ids, f)
        self.destroy()

    def apply(self):
        team = self.var_combo_teams.get()
        if not self.match_ids.get(team):
            self.match_ids[team] = {}
        self.match_ids[team][self.values_combo_persons[self.var_combo_persons.get()]] = self.entry_uuid.get()

    def autofill_persons(self):
        self.values_combo_persons = {datas['name']: datas['ID']
                                     for datas in self.dispodaten[self.var_combo_teams.get()]['clowndaten']}
        self.combo_persons.config(values=list(self.values_combo_persons))



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


class Login(CommonTopLevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.lift(parent)
        self.bind('<Return>', lambda event: self.login_progress())

        self.access_data = {}

        self.lb_combo_persons = tk.Label(self.frame_combo_select, text='Person auswählen')
        self.lb_combo_persons.pack(pady=(0, 5))
        self.var_combo_persons = tk.StringVar()
        self.values_combo_persons = self.get_login_persons()
        self.combo_persons = ttk.Combobox(self.frame_combo_select, values=self.values_combo_persons,
                                          textvariable=self.var_combo_persons)
        self.combo_persons.bind("<<ComboboxSelected>>", lambda event: self.autofill())
        self.combo_persons.pack(pady=(5, 0))

        self.lb_entry_email = tk.Label(self.frame_input, text='Email')
        self.lb_entry_email.grid(row=0, column=0, padx=(0, 5), pady=(0, 5), sticky='w')
        self.entry_email = tk.Entry(self.frame_input)
        self.entry_email.grid(row=0, column=1, padx=(5, 0), pady=(0, 5))
        self.lb_entry_password = tk.Label(self.frame_input, text='Password')
        self.lb_entry_password.grid(row=1, column=0, padx=(0, 5), pady=(5, 5), sticky='w')
        self.entry_password = tk.Entry(self.frame_input, show='*')
        self.entry_password.grid(row=1, column=1, padx=(5, 0), pady=(5, 5))

        self.var_chk_save_access_data = tk.BooleanVar(value=False)
        self.chk_save_access_data = tk.Checkbutton(self.frame_input, text='Zugangsdaten speichern?',
                                                   variable=self.var_chk_save_access_data)
        self.chk_save_access_data.grid(row=3, column=0, columnspan=2, pady=(5, 0))

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=15, command=self.login_progress)
        self.bt_ok.grid(row=0, column=0, padx=(0, 5), pady=(0, 0), sticky='e')
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, padx=(5, 0), pady=(0, 0), sticky='w')

        self.get_login_persons()

    def login_progress(self):
        progressbar = ProgressIndeterm(self, 'Warten auf Login...')
        progressbar.start()
        t = threading.Thread(target=self.login, args=[progressbar])
        t.start()

    def login(self, progressbar: ProgressIndeterm):  # für das Endanwender-Programm: Logik und allgemeines Login auf Server. Server gibt alle Token und Rechte zurück.
        email = (self.entry_email.get()).lower()
        password = self.entry_password.get()

        response = requests.post(f'{self.parent.host}/token', data={'username': email, 'password': password})
        print(response)
        try:
            payload = jwt.decode(response.json()['access_token'], options={"verify_signature": False})
        except KeyError as e:
            progressbar.stop()
            progressbar.destroy()
            tk.messagebox.showerror(parent=self.parent, title='Login',
                                    message='Ich konnte Sie nicht erfolgreich autorisieren.')
            return

        self.parent.access_token = response.json()['access_token']
        self.parent.authorizations = payload["roles"]

        progressbar.stop()
        progressbar.destroy()
        tk.messagebox.showinfo(parent=self, title='Info',
                               message=f'Eingelogged als:\n'
                                       f'- {", ".join(payload["roles"])}')
        if self.var_chk_save_access_data.get():
            with open('access_data.json', 'w') as f:
                if not (person := self.var_combo_persons.get()):
                    tk.messagebox.showerror(parent=self, message='Sie müssen zuerst ihren Namen eintragen.')
                self.access_data[person] = {}
                self.access_data[person]['email'] = self.entry_email.get()
                self.access_data[person]['password'] = self.entry_password.get()
                json.dump(self.access_data, f)
        self.destroy()

    def get_login_persons(self):
        try:
            with open('access_data.json', 'r') as f:
                self.access_data = json.load(f)
        except Exception as e:
            print(e)
            return
        return list(self.access_data)

    def autofill(self):
        if not self.var_combo_persons.get():
            return
        email = self.access_data[self.var_combo_persons.get()]['email']
        password = self.access_data[self.var_combo_persons.get()]['password']
        self.entry_email.delete(0, 'end')
        self.entry_email.insert(0, email)
        self.entry_password.delete(0, 'end')
        self.entry_password.insert(0, password)


class CreateNewProject(CommonTopLevel):
    def __init__(self, parent, access_token: str):
        super().__init__(parent)

        self.access_token = access_token

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

        self.lb_username_admin = tk.Label(self.frame_input, text='Username Admin:')
        self.lb_username_admin.grid(row=4, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
        self.entry_username_admin = PlaceholderEntry(self.frame_input, width=50,
                                                     placeholder='Bitte einen Nutzernamen einfügen.')
        self.entry_username_admin.grid(row=4, column=1, sticky='w', padx=(5, 0), pady=(5, 5))
        self.lb_entry_password_admin = tk.Label(self.frame_input, text='Passwort Admin:')
        self.lb_entry_password_admin.grid(row=5, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
        self.entry_password_admin = PlaceholderEntry(master=self.frame_input, width=50, show='*',
                                                     placeholder='Wenn leer: Random Passwort wird erzeugt.')
        self.entry_password_admin.grid(row=5, column=1, sticky='w', padx=(5, 0), pady=(5, 5))
        self.var_chk_active = tk.BooleanVar(value=True)
        self.chk_active = tk.Checkbutton(self.frame_input, text='Soll das Projekt auf activ gesetzt werden?',
                                         variable=self.var_chk_active)
        self.chk_active.grid(row=6, column=0, columnspan=2, pady=(5, 5))

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=20, command=self.new_project)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 10))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=20, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(10, 0))

    def new_project(self):
        person = pm.PersonCreate(f_name=self.entry_fname_admin.get(), l_name=self.entry_lname_admin.get(),
                                 email=EmailStr(self.entry_email_admin.get()), password=self.entry_password_admin.get(),
                                 username=self.entry_username_admin.get())
        project = pm.ProjectCreate(name=self.entry_projectname.get(), active=self.var_chk_active.get())

        token = pm.Token(access_token=self.access_token, token_type='bearer')
        response = requests.post(f'{self.parent.host}/su/account',
                                 json={'person': person.dict(), 'project': project.dict()},
                                 headers={'Authorization': f'Bearer {self.access_token}'})
        self.parent.new_project_data = response.json()
        self.destroy()


class DeleteAccount(CommonTopLevel):
    def __init__(self, parent, access_token: str):
        super().__init__(parent)

        self.parent = parent
        self.access_token = access_token

        self.project = self.get_project()

        self.lb_delete_advice = tk.Label(self.frame_input,
                                         text=f'Sie sind im Begriff, ihren Account\nName: "{self.project.name}"\n'
                                              f'zu löschen.\nEs werden dabei alle mit dem Account verbundenen Daten '
                                              f'unwiederruflich gelöscht.\nWenn Sie dies möchten, geben Sie bitte '
                                              f'in die nachstehenden Felder den Namen ihres Accounts sowie die\n'
                                              f'ID: "{self.project.id}"\nein.',
                                         justify='left', wraplength=350)
        self.lb_delete_advice.pack()

        self.frame_entrys = ttk.Frame(self.frame_input)
        self.frame_entrys.pack()

        self.lb_name = tk.Label(self.frame_entrys, text='Account-Name:')
        self.lb_name.grid(row=0, column=0, sticky='w', pady=(10, 0))
        self.entry_name = tk.Entry(self.frame_entrys, width=60)
        self.entry_name.grid(row=1, column=0, sticky='w', pady=(0, 5))
        self.lb_id = tk.Label(self.frame_entrys, text='Account-ID:')
        self.lb_id.grid(row=2, column=0, sticky='w', pady=(5, 0))
        self.entry_id = tk.Entry(self.frame_entrys, width=60)
        self.entry_id.grid(row=3, column=0, sticky='w', pady=(0, 10))

        self.bt_ok = tk.Button(self.frame_buttons, text='Löschen', width=20, command=self.delete_account)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=20, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(5, 0))

    def delete_account(self):
        if self.entry_name.get() != self.project.name or self.entry_id.get() != str(self.project.id):
            tk.messagebox.showerror(parent=self,
                                    message='Die Einträge für Account-Name bzw. Account-ID sind nicht korrekt.')
        else:
            if not tk.messagebox.askyesno(parent=self,
                                          message=f'Möchten Sie ihren Account "{self.project.name}" mit allen '
                                                  f'damit verbundenen Daten wirklich entgültig löschen?\n'
                                                  f'(Dieser Vorgang kann nicht rückgängig gemacht werden.)'):
                return
            response = requests.delete(f'{self.parent.host}/admin/account',
                                       params={'project_id': self.project.id},
                                       headers={'Authorization': f'Bearer {self.access_token}'})
            try:
                deleted_project = pm.Project.parse_obj(response.json())
                tk.messagebox.showinfo(parent=self,
                                       message=f'Der Account {deleted_project.name} wurde vollständig entfernt.')
                self.destroy()
                return
            except Exception as e:
                tk.messagebox.showerror(parent=self, message=f'Fehler: {response.text}, Exception: {e}')
                return

    def get_project(self):
        response = requests.get(f'{self.parent.host}/admin/project',
                                headers={'Authorization': f'Bearer {self.access_token}'})
        try:
            project = pm.Project.parse_obj(response.json())
            print(project)
            return project
        except Exception as e:
            tk.messagebox.showerror(parent=self, message=f'{response.text}\nFehler: {e}')
            return


class ChangeProjectName(CommonTopLevel):
    def __init__(self, parent, access_token):
        super().__init__(parent=parent)
        self.bind('<Return>', lambda event: self.change())

        self.access_token = access_token
        self.old_name = None

        self.lb_name = tk.Label(self.frame_input, text='Projektname:')
        self.lb_name.pack()
        self.entry_name = tk.Entry(self.frame_input, width=40)
        self.entry_name.pack()

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=20, command=self.change)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=20, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(5, 0))

        self.autofill()

    def change(self):
        new_name = self.entry_name.get()
        if new_name == self.old_name:
            self.destroy()
            tk.messagebox.showinfo(parent=self.parent, message='Der Projektname wurde nicht verändert.')
            return

        response = requests.put(f'{self.parent.host}/admin/project',
                                params={'new_name': self.entry_name.get()},
                                headers={'Authorization': f'Bearer {self.access_token}'})
        self.destroy()
        tk.messagebox.showinfo(parent=self.parent,
                               message=f'Der Projektname wurde von "{self.old_name}" zu "{new_name} geändert."')

    def autofill(self):
        response = requests.get(f'{self.parent.host}/admin/project',
                                headers={'Authorization': f'Bearer {self.access_token}'})
        self.old_name = response.json()['name']
        self.entry_name.insert(0, self.old_name)


class CreatePerson(CommonTopLevel):
    def __init__(self, parent, access_token: str):
        super().__init__(parent)

        self.access_token = access_token

        self.lb_fname = tk.Label(self.frame_input, text='Vorname:')
        self.lb_fname.grid(row=0, column=0, sticky='e', padx=(0, 5), pady=(0, 5))
        self.entry_fname = tk.Entry(self.frame_input, width=50)
        self.entry_fname.grid(row=0, column=1, sticky='w', padx=(5, 0), pady=(0, 5))
        self.lb_lname = tk.Label(self.frame_input, text='Nachname:')
        self.lb_lname.grid(row=1, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
        self.entry_lname = tk.Entry(self.frame_input, width=50)
        self.entry_lname.grid(row=1, column=1, sticky='w', padx=(5, 0), pady=(5, 5))
        self.lb_email = tk.Label(self.frame_input, text='Email:')
        self.lb_email.grid(row=2, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
        self.entry_email = tk.Entry(self.frame_input, width=50)
        self.entry_email.grid(row=2, column=1, sticky='w', padx=(5, 0), pady=(5, 5))
        self.lb_password = tk.Label(self.frame_input, text='Passwort')
        self.lb_password.grid(row=3, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
        self.entry_password = PlaceholderEntry(self.frame_input, width=50, show='*',
                                            placeholder='Wenn leer: Random Passwort wird erzeugt.')
        self.entry_password.grid(row=3, column=1, sticky='w', padx=(5, 0), pady=(5, 0))

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=20, command=self.new_person)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 10))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=20, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(10, 0))

    def new_person(self):
        person = pm.PersonCreate(f_name=self.entry_fname.get(), l_name=self.entry_lname.get(),
                                 email=EmailStr(self.entry_email.get()), username=EmailStr(self.entry_email.get()),
                                 password=self.entry_password.get())
        response = requests.post(f'{self.parent.host}/admin/person',
                                 json=person.dict(),
                                 headers={'Authorization': f'Bearer {self.access_token}'})
        self.parent.new_person_data = response.json()
        self.destroy()


class ChangePersonNames(CommonTopLevel):
    def __init__(self, parent, access_token):
        super().__init__(parent)

        self.access_token = access_token
        self.all_persons = self.get_persons()
        self.all_persons__dict_name_person_show: dict[str, pm.PersonShow] = {f'{p.f_name} {p.l_name}': p
                                                                             for p in self.all_persons}
        self.var_combo_persons = tk.StringVar()

        self.lb_combo_persons = tk.Label(self.frame_combo_select, text='Personen:')
        self.combo_persons = ttk.Combobox(self.frame_combo_select, values=list(self.all_persons__dict_name_person_show),
                                          textvariable=self.var_combo_persons, state='readonly')
        self.combo_persons.bind('<<ComboboxSelected>>', lambda event: self.new_selection_person())
        self.lb_combo_persons.grid(row=0, column=0)
        self.combo_persons.grid(row=0, column=1)

        self.lb_f_name = tk.Label(self.frame_input, text='Vorname:')
        self.entry_f_name = tk.Entry(self.frame_input)
        self.lb_l_name = tk.Label(self.frame_input, text='Nachname:')
        self.entry_l_name = tk.Entry(self.frame_input)
        self.lb_f_name.grid(row=0, column=0)
        self.entry_f_name.grid(row=0, column=1)
        self.lb_l_name.grid(row=1, column=0)
        self.entry_l_name.grid(row=1, column=1)

        self.bt_ok = tk.Button(self.frame_buttons, text='Ändern', command=self.update_to_db)
        self.bt_cancel = tk.Button(self.frame_buttons, text='Abbruch', command=self.destroy)
        self.bt_ok.grid(row=0, column=0)
        self.bt_cancel.grid(row=0, column=1)

    def get_persons(self) -> list[pm.PersonShow] | None:
        response = requests.get(f'{self.parent.host}/admin/persons',
                                headers={'Authorization': f'Bearer {self.access_token}'})
        try:
            all_persons: list[pm.PersonShow] = sorted([pm.PersonShow(**p)
                                                       for p in response.json()], key=lambda p: p.f_name)
            return all_persons
        except Exception as e:
            tk.messagebox.showerror('Personennamen ändern', f'Fehler: {response.json()}, {e}')
            return

    def new_selection_person(self):
        person = self.all_persons__dict_name_person_show[self.combo_persons.get()]
        self.entry_f_name.delete(0, 'end')
        self.entry_l_name.delete(0, 'end')
        self.entry_f_name.insert(0, person.f_name)
        self.entry_l_name.insert(0, person.l_name)

    def update_to_db(self):

        person = self.all_persons__dict_name_person_show.get(self.combo_persons.get())
        if not person:
            return
        person.f_name = self.entry_f_name.get()
        person.l_name = self.entry_l_name.get()
        person_json = json.loads(person.json())
        print(person.f_name, person.l_name)
        print(person_json)

        response = requests.put(f'{self.parent.host}/admin/person', json=person_json,
                                headers={'Authorization': f'Bearer {self.access_token}'})
        self.parent.new_person_data = response.json()
        self.destroy()


class AssignPersonToPosition(CommonTopLevel):
    def __init__(self, parent, access_token: str):
        super().__init__(parent)
        self.bind('<Return>', lambda event: self.update_to_db())

        self.access_token = access_token

        self.id_of_old_amin = None
        self.id_of_actual_admin = None

        self.all_persons = self.get_persons()
        self.all_teams = self.get_teams()
        self.all_persons_dict_for_combo: dict[str, pm.PersonShow] = self.make_dict_for_widgets('person')
        self.all_teams_dict_for_radio_chk: dict[str: str] = self.make_dict_for_widgets('team')

        self.all_checks_team = {}
        self.vars_all_checks_team = {}

        self.var_combo_persons = tk.StringVar()
        self.var_chk_admin = tk.BooleanVar()
        self.var_radio_teams_actor = tk.StringVar(value='kein Team')

        '''Widget for selections'''
        self.lb_combo_persons = tk.Label(self.frame_input, text='Mitarbeiter:in:')
        self.lb_combo_persons.grid(row=0, column=0, sticky='e', padx=(0, 5), pady=(0, 5))
        self.combo_persons = ttk.Combobox(self.frame_input, values=list(self.all_persons_dict_for_combo),
                                          textvariable=self.var_combo_persons, state='readonly')
        self.combo_persons.bind('<<ComboboxSelected>>', lambda event: self.new_selection_person())
        self.combo_persons.grid(row=0, column=1, sticky='w', padx=(5, 0), pady=(0, 5))

        self.frame_checks = ttk.Frame(self.frame_input, padding='00 10 00 00')
        self.frame_checks.grid(row=1, column=0, columnspan=2)

        self.chk_admin = tk.Checkbutton(self.frame_checks,
                                        text=f'... ist Admin für Projekt {self.all_persons[0].project.name}.',
                                        variable=self.var_chk_admin, command=self.new_selection_admin)
        self.chk_admin.grid(row=0, column=0, columnspan=3)

        tk.Label(self.frame_checks, text='Spieler:in').grid(row=1, column=1, sticky='w', padx=(5, 5), pady=(10, 5))
        tk.Label(self.frame_checks, text='Planer:in').grid(row=1, column=2, sticky='w', padx=(5, 5), pady=(10, 5))
        for i, (id_team, team) in enumerate(self.all_teams_dict_for_radio_chk.items(), start=2):
            tk.Label(self.frame_checks,
                     text=f'Team {team.name}').grid(row=i, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
            radio_actor = tk.Radiobutton(self.frame_checks, variable=self.var_radio_teams_actor, value=id_team,
                           command=lambda id_t=id_team: self.new_selection_team(profession='actor', id_team=id_t))
            radio_actor.grid(row=i, column=1, padx=5, pady=5)
            self.vars_all_checks_team[id_team] = tk.BooleanVar()
            self.all_checks_team[id_team] = tk.Checkbutton(self.frame_checks,
                                                           variable=self.vars_all_checks_team[id_team],
                                                           command=lambda id_t=id_team: self.new_selection_team('dispatcher', id_t))
            self.all_checks_team[id_team].grid(row=i, column=2, padx=(5, 0), pady=5)
        tk.Label(self.frame_checks, text=f'Keinem Team zugeordnet').grid(row=len(self.all_teams)+2, column=0,
                                                                         sticky='e', padx=(0, 5), pady=(5, 0))
        tk.Radiobutton(self.frame_checks, variable=self.var_radio_teams_actor, value='kein Team',
                       command=lambda: self.new_selection_team(profession='actor', id_team='-1')).grid(row=len(self.all_teams)+2,
                                                                                         column=1, padx=5, pady=(5, 0))

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=15, command=self.update_to_db)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(5, 0))

    def update_to_db(self):
        all_persons = {k: json.loads(v.json()) for k, v in self.all_persons_dict_for_combo.items()}

        new_jobs = []

        for person in all_persons.values():
            response = requests.put(f'{self.parent.host}/admin/person', json=person,
                                    headers={'Authorization': f'Bearer {self.access_token}'})
            new_jobs.append(response.json())

        if self.id_of_old_amin != self.id_of_actual_admin:
            self.parent.access_token = None
            self.parent.authorizations = []
            new_admin = [p for p in self.all_persons if p.id == self.id_of_actual_admin][0]
            tk.messagebox.showwarning(parent=self, title='Admin Login',
                                      message=f'Sie wurden als Admin ausgeloggt. Neuer Admin des Projekts ist:\n'
                                              f'"{new_admin.f_name} {new_admin.l_name}."')
        self.parent.new_jobs = new_jobs
        self.destroy()

    def new_selection_person(self):
        selected = self.var_combo_persons.get()
        person = self.all_persons_dict_for_combo[selected]

        if person.project_of_admin:
            self.var_chk_admin.set(True)
        else:
            self.var_chk_admin.set(False)

        if team := person.team_of_actor:
            self.var_radio_teams_actor.set(str(team.id))
        else:
            self.var_radio_teams_actor.set('kein Team')

        for var_chk_bt in self.vars_all_checks_team.values():
            var_chk_bt.set(False)
        if person.teams_of_dispatcher:
            for team in person.teams_of_dispatcher:
                self.vars_all_checks_team[str(team.id)].set(True)

    def new_selection_admin(self):
        if not self.var_combo_persons.get():
            self.var_chk_admin.set(False)
            return

        selected_person = self.all_persons_dict_for_combo[self.var_combo_persons.get()]
        if self.var_chk_admin.get():
            for p in self.all_persons:
                if p == selected_person:
                    continue
                if p.project_of_admin:
                    if not tk.messagebox.askyesno(parent=self,
                                                  message=f'"{p.f_name} {p.l_name}" ist bereits Admin des Projekts.\n'
                                                          f'Wollen Sie diese Position "{selected_person.f_name} '
                                                          f'{selected_person.l_name}" neu zuordnen?'):
                        self.var_chk_admin.set(False)
                        return
                    selected_person.project_of_admin = selected_person.project
                    self.id_of_actual_admin = selected_person.id
                    self.id_of_old_amin = p.id
                    p.project_of_admin = None

                    return
        else:
            tk.messagebox.showinfo(parent=self, message=f'Es muss genau einen Admin für Ihr Projekt vorhanden sein.\n'
                                                        f'Um diese Position einem anderen Mitarbeiter zuzuordnen,'
                                                        f'wählen Sie bitte diesen Mitarbeiter aus.')
            self.var_chk_admin.set(True)
            return

    def new_selection_team(self, profession: Literal['actor', 'dispatcher'], id_team):
        person_fullname = self.var_combo_persons.get()

        if person_fullname:
            person = self.all_persons_dict_for_combo[person_fullname]

        if profession == 'actor':
            if not person_fullname:
                self.var_radio_teams_actor.set('kein Team')
                return
            team_id: str = self.var_radio_teams_actor.get()
            person.team_of_actor = self.all_teams_dict_for_radio_chk.get(team_id)
            return

        if profession == 'dispatcher':
            if not person_fullname:
                for var in self.vars_all_checks_team.values():
                    var.set(False)
                return
            if not self.vars_all_checks_team[id_team].get():
                tk.messagebox.showerror(parent=self,
                                        message='Um für dieses Team den Dispatcher zu wechseln, wählen Sie die '
                                                'entsprechende Person und weisen dem Team diese als Dispatcher zu')
                self.vars_all_checks_team[id_team].set(True)
            for p in self.all_persons_dict_for_combo.values():
                if p == person:
                    continue
                if id_team in (disp_teams := {str(t.id): t for t in p.teams_of_dispatcher}):
                    if tk.messagebox.askyesno(parent=self,
                                              message=f'Der/die Planer:in des Teams "{disp_teams[id_team].name}" '
                                                      f'ist zurzeit "{p.f_name} {p.l_name}".\n'
                                                      f'Soll diese Position mit "{person.f_name} {person.l_name}" '
                                                      f'neu besetzt werden?'):
                        p.teams_of_dispatcher.remove(disp_teams[id_team])
                        person.teams_of_dispatcher.append(disp_teams[id_team])
                    else:
                        self.vars_all_checks_team[id_team].set(False)

    def get_persons(self):
        response = requests.get(f'{self.parent.host}/admin/persons',
                                headers={'Authorization': f'Bearer {self.access_token}'})
        try:
            all_persons = sorted([pm.PersonShow(**p) for p in response.json()], key=lambda p: p.f_name)
            return all_persons
        except Exception as e:
            return response.json(), e

    def get_teams(self):
        response = requests.get(f'{self.parent.host}/admin/teams',
                                headers={'Authorization': f'Bearer {self.access_token}'})
        data = response.json()
        if type(data) == dict and data.get('status_code') == 401:
            tk.messagebox.showerror(parent=self, message='Nicht authorisiert!')
            self.destroy()

        return sorted([pm.Team(**team) for team in data], key=lambda t: t.name)

    def make_dict_for_widgets(self, combo_type: Literal['person', 'team']):
        if combo_type == 'person':
            return {f'{p.f_name} {p.l_name}': p for p in self.all_persons}
        if combo_type == 'team':
            return {str(t.id): t for t in self.all_teams}


class DeleteTeam(CommonTopLevel):
    def __init__(self, parent, access_token):
        super().__init__(parent)

        self.access_token = access_token
        self.all_teams = self.get_teams()
        self.all_teams_dict_for_combo = {t.name: t for t in self.all_teams}

        self.var_combo_teams = tk.StringVar()

        self.lb_combo_teams = tk.Label(self.frame_input, text='Auswahl Team:')
        self.lb_combo_teams.grid(row=0, column=0, sticky='e', padx=(0, 0), pady=(0, 5))
        self.combo_teams = ttk.Combobox(self.frame_input, values=list(self.all_teams_dict_for_combo),
                                        textvariable=self.var_combo_teams, state='readonly')
        self.combo_teams.grid(row=0, column=1, sticky='w', padx=(0, 0), pady=(0, 5))

        self.bt_ok = tk.Button(self.frame_buttons, text='Löschen', width=15, command=self.delete_team)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(5, 0))

    def delete_team(self):
        team = self.all_teams_dict_for_combo[self.var_combo_teams.get()]
        if not tk.messagebox.askokcancel(parent=self,
                                         message=f'Achtung!!!\n{team.name} wird unwiderruflich aus der Datenbank '
                                                 f'gelöscht.\nDies kann nicht rückgängig gemacht werden.'):
            return

        response = requests.delete(f'{self.parent.host}/admin/team',
                                   params={'team_id': team.id},
                                   headers={'Authorization': f'Bearer {self.access_token}'})

        try:
            deleted_team = pm.Team.parse_obj(response.json())
            tk.messagebox.showinfo(parent=self,
                                   message=f'Das Team "{deleted_team.name}" mit allen verbundenen Planperioden wurde '
                                           f'aus der Datenbank gelöscht.')
            self.destroy()
            return
        except Exception as e:
            tk.messagebox.showinfo(parent=self, message=f'Fehler: {response.json()}\nException: {e}')
            self.destroy()

    def get_teams(self):
        return sorted(HelperRequests.get_teams_admin(self, self.parent.host, self.access_token), key=lambda t: t.name)


class DeletePerson(CommonTopLevel):
    def __init__(self, parent, access_token):
        super().__init__(parent)

        self.access_token = access_token
        self.all_persons = self.get_persons()
        self.all_persons_dict_for_combo = {f'{p.f_name} {p.l_name}': p for p in self.all_persons}

        self.var_combo_persons = tk.StringVar()

        self.lb_combo_persons = tk.Label(self.frame_input, text='Mitarbeiter:in:')
        self.lb_combo_persons.grid(row=0, column=0, sticky='e', padx=(0, 0), pady=(0, 5))
        self.combo_persons = ttk.Combobox(self.frame_input, values=list(self.all_persons_dict_for_combo),
                                          textvariable=self.var_combo_persons, state='readonly')
        self.combo_persons.grid(row=0, column=1, sticky='w', padx=(0, 0), pady=(0, 5))

        self.bt_ok = tk.Button(self.frame_buttons, text='Löschen', width=15, command=self.delete_person)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(5, 0))

    def delete_person(self):
        person = self.all_persons_dict_for_combo[self.var_combo_persons.get()]
        if not tk.messagebox.askokcancel(parent=self,
                                         message=f'Achtung!!!\n{person.f_name} {person.l_name} wird unwiderruflich '
                                                 f'aus der Datenbank gelöscht.\nDies kann nicht rückgängig gemacht '
                                                 f'werden.'):
            return

        response = requests.delete(f'{self.parent.host}/admin/person',
                                   params={'person_id': person.id},
                                   headers={'Authorization': f'Bearer {self.access_token}'})

        try:
            deleted_person = pm.Person(**response.json())
            tk.messagebox.showinfo(parent=self,
                                   message=f'Der/die Mitarbeiter:in "{deleted_person.f_name} {deleted_person.l_name}" '
                                           f'wurde aus der Datenbank gelöscht.')
            self.destroy()
            return
        except Exception as e:
            tk.messagebox.showinfo(parent=self, message=f'Fehler {response.json()}\nException {e}')
        self.destroy()

    def get_persons(self):
        response = requests.get(f'{self.parent.host}/admin/persons',
                                headers={'Authorization': f'Bearer {self.access_token}'})
        try:
            all_persons = sorted([pm.PersonShow(**p) for p in response.json()], key=lambda p: p.f_name)
            return all_persons
        except Exception as e:
            tk.messagebox.showerror(parent=self, message=f'Ein Fehler trat auf: {e}')


class ChangePlanPeriod(CommonTopLevel):
    def __init__(self, parent, access_token: str):
        super().__init__(parent)
        self.bind('<Return>', lambda event: self.change())

        self.access_token = access_token

        self.frame_combo_select.config(padding='20 20 20 20')

        self.var_chk_closed = tk.BooleanVar()
        self.var_combo_planperiods = tk.StringVar()
        self.var_combo_teams = tk.StringVar()
        self.values_combo_teams = {t.name: str(t.id)
                                   for t in HelperRequests.get_teams_dispatcher(self, parent.host, self.access_token)}
        self.values_combo_planperiods: dict[str, pm.PlanPeriod] = {}

        self.lb_combo_teams = tk.Label(self.frame_combo_select, text='Team')
        self.lb_combo_teams.grid(row=0, column=0, sticky='w')
        self.combo_teams = ttk.Combobox(self.frame_combo_select, values=list(self.values_combo_teams),
                                        textvariable=self.var_combo_teams, state='readonly')
        self.combo_teams.bind('<<ComboboxSelected>>', lambda event: self.autofill('team'))
        self.combo_teams.grid(row=1, column=0, padx=(0, 5))

        self.lb_combo_planperiods = tk.Label(self.frame_combo_select, text='Planperiode:')
        self.lb_combo_planperiods.grid(row=0, column=1, sticky='w', padx=(5, 0))
        self.combo_planperiods = ttk.Combobox(self.frame_combo_select, values=[],
                                              textvariable=self.var_combo_planperiods, state='readonly')
        self.combo_planperiods.bind('<<ComboboxSelected>>', lambda event: self.autofill('planperiod'))
        self.combo_planperiods.grid(row=1, column=1, padx=(5, 0))

        self.chk_closed = tk.Checkbutton(self.frame_input, text='Eingabe von Spieloptionen nicht mehr möglich.',
                                         variable=self.var_chk_closed)
        self.chk_closed.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        self.lb_start = tk.Label(self.frame_input, text='Anfang:')
        self.lb_start.grid(row=1, column=0, sticky='w', padx=(5, 5))
        self.lb_end = tk.Label(self.frame_input, text='Ende:')
        self.lb_end.grid(row=1, column=1, sticky='w', padx=(5, 5))
        self.lb_deadline = tk.Label(self.frame_input, text='Deadline:')
        self.lb_deadline.grid(row=1, column=2, sticky='w', padx=(5, 5))
        self.start = tkcalendar.DateEntry(self.frame_input, locale='de_De', width=20, date_pattern='dd.mm.yyyy')
        self.start.grid(row=2, column=0, sticky='w', padx=(5, 5))
        self.end = tkcalendar.DateEntry(self.frame_input, locale='de_De', width=20, date_pattern='dd.mm.yyyy')
        self.end.grid(row=2, column=1, sticky='w', padx=(5, 5))
        self.deadline = tkcalendar.DateEntry(self.frame_input, locale='de_De', width=20, date_pattern='dd.mm.yyyy')
        self.deadline.grid(row=2, column=2, sticky='w', padx=(5, 5))

        self.lb_notes = tk.Label(self.frame_input, text='Notizen:')
        self.lb_notes.grid(row=3, column=0, columnspan=3, sticky='w', pady=(10, 0))
        self.text_notes = tk.Text(self.frame_input, width=50, height=5)
        self.text_notes.grid(row=4, column=0, columnspan=3, sticky='ew')

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=20, command=self.change)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=20, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(5, 0))

        self.var_combo_teams.set(list(self.values_combo_teams)[0])
        self.autofill('team')

    def change(self):
        if not self.var_combo_planperiods.get():
            tk.messagebox.showinfo(parent=self, message='Bitte wählen Sie zuest eine Planperiode aus.')
            return
        planperiod: pm.PlanPeriod = self.values_combo_planperiods[self.var_combo_planperiods.get()]
        planperiod.start = self.start.get_date()
        planperiod.end = self.end.get_date()
        planperiod.deadline = self.deadline.get_date()
        planperiod.closed = self.var_chk_closed.get()
        planperiod.notes = self.text_notes.get(1.0, 'end')
        planperiod = json.loads(planperiod.json())

        response = requests.put(f'{self.parent.host}/dispatcher/planperiod',
                                json=planperiod,
                                headers={'Authorization': f'Bearer {self.access_token}'})
        try:
            new_planperiod = pm.PlanPeriod.parse_obj(response.json())
            self.destroy()
            tk.messagebox.showinfo(parent=self.parent, message='Update war erfolgreich.')
        except Exception as e:
            self.destroy()
            tk.messagebox.showerror(parent=self.parent, message=f'Ein fehler trat auf:\n{response.json()}\n{e}')

    def autofill(self, box: Literal['team', 'planperiod']):
        if box == 'team':
            team_id = self.values_combo_teams[self.var_combo_teams.get()]
            planperiods = HelperRequests.get_planperiods(self, self.parent.host, self.access_token, team_id)
            self.values_combo_planperiods = {f'{pp.start.strftime("%d.%m.%y")} - {pp.end.strftime("%d.%m.%y")}': pp
                                             for pp in planperiods}
            self.combo_planperiods.config(values=list(self.values_combo_planperiods))

            if self.values_combo_planperiods:
                self.var_combo_planperiods.set(list(self.values_combo_planperiods)[0])
                self.autofill('planperiod')

        if box == 'planperiod':
            start = self.values_combo_planperiods[self.var_combo_planperiods.get()].start
            end = self.values_combo_planperiods[self.var_combo_planperiods.get()].end
            deadline = self.values_combo_planperiods[self.var_combo_planperiods.get()].deadline
            closed = self.values_combo_planperiods[self.var_combo_planperiods.get()].closed
            notes = self.values_combo_planperiods[self.var_combo_planperiods.get()].notes
            keys_values_planperiods = list(self.values_combo_planperiods)
            if (curr_index := keys_values_planperiods.index(self.var_combo_planperiods.get())) > 0:
                maxdate = (self.values_combo_planperiods[keys_values_planperiods[curr_index-1]].start
                           - datetime.timedelta(days=1))
            else:
                maxdate = None
            if curr_index < len(keys_values_planperiods) - 1:
                mindate = (self.values_combo_planperiods[keys_values_planperiods[curr_index+1]].end
                           + datetime.timedelta(days=1))
            else:
                mindate = None
            self.start.config(mindate=mindate, maxdate=maxdate)
            self.end.config(mindate=mindate, maxdate=maxdate)
            self.start.set_date(start)
            self.end.set_date(end)
            self.deadline.set_date(deadline)
            self.var_chk_closed.set(closed)
            self.text_notes.delete(1.0, 'end')
            self.text_notes.insert(1.0, notes)


class GetAvailDays(CommonTopLevel):
    def __init__(self, parent, host: str, access_token: str):
        super().__init__(parent)

        self.host = host

        self.access_token = access_token

        self.all_teams_dict = {t.name: t for t in sorted(HelperRequests.get_teams_dispatcher(self, host, access_token),
                                                         key=lambda t: t.name)}
        self.all_planperiods = {}

        self.var_combo_teams = tk.StringVar()
        self.var_combo_planperiods = tk.StringVar()

        self.frame_combo_select.config(padding='20 20 20 20')

        self.lb_combo_teams = tk.Label(self.frame_combo_select, text='Auswahl Team:')
        self.lb_combo_teams.grid(row=0, column=0, sticky='w')
        self.combo_teams = ttk.Combobox(self.frame_combo_select, values=list(self.all_teams_dict),
                                        textvariable=self.var_combo_teams)
        self.combo_teams.bind('<<ComboboxSelected>>', lambda event: self.autofill_planperiods())
        self.combo_teams.grid(row=1, column=0, sticky='w', padx=(0, 5))
        self.lb_combo_planperiods = tk.Label(self.frame_combo_select, text='Auswahl Planperiode:')
        self.lb_combo_planperiods.grid(row=0, column=1, sticky='w')
        self.combo_planperiods = ttk.Combobox(self.frame_combo_select, textvariable=self.var_combo_planperiods)
        self.combo_planperiods.grid(row=1, column=1, sticky='w', padx=(5, 0))

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=15, command=self.get_avail_days)
        self.bt_ok.grid(row=0, column=0, padx=(0, 5), pady=(10, 0))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, padx=(5, 0), pady=(10, 0))

    def get_avail_days(self):
        if not self.var_combo_planperiods.get():
            tk.messagebox.showerror(parent=self, message='Bitte zuerst eine Planperiode auswählen.')
            return
        planperiod_id = self.all_planperiods[self.var_combo_planperiods.get()].id
        response = requests.get(f'{self.host}/dispatcher/avail_days',
                                params={'planperiod_id': planperiod_id},
                                headers={'Authorization': f'Bearer {self.access_token}'})
        avail_days = response.json()
        try:
            avail_days = {person_id: {'days': [pm.AvailDay.parse_obj(ad) for ad in av_days['days']], 'notes': av_days['notes']}
                          for person_id, av_days in avail_days.items()}
            self.parent.avail_days = avail_days
            self.destroy()
        except Exception as e:
            tk.messagebox.showinfo(parent=self, message=f'Fehler {response.json()}\nException {e}')
        self.destroy()

    def autofill_planperiods(self):
        team = self.all_teams_dict[self.var_combo_teams.get()]
        planperiods = sorted(HelperRequests.get_planperiods(self.parent, self.host, self.access_token, team.id),
                             key=lambda pp: pp.start)
        self.all_planperiods = {f'{pp.start.strftime("%d.%m.%y")} - {pp.end.strftime("%d.%m.%y")}': pp
                                for pp in planperiods if pp.closed}
        if not self.all_planperiods:
            tk.messagebox.showinfo(parent=self, message=f'Keine Planperioden abrufbar.')
            return
        values = list(self.all_planperiods)
        self.combo_planperiods.config(values=values)
        self.var_combo_planperiods.set(values[0])


class CreateTeam(CommonTopLevel):
    def __init__(self, parent, access_token: str):
        super().__init__(parent)
        self.bind('<Return>', lambda event: self.create())

        self.access_token = access_token
        self.lb_name = tk.Label(self.frame_input, text='Name Team:')
        self.lb_name.grid(row=0, column=0, sticky='e', padx=(0, 5), pady=(0, 5))
        self.entry_name = tk.Entry(self.frame_input, width=50)
        self.entry_name.grid(row=0, column=1, sticky='w', padx=(5, 0), pady=(0, 5))

        self.lb_dispatcher = tk.Label(self.frame_input, text='Auswahl Planer:in')
        self.lb_dispatcher.grid(row=1, column=0, sticky='e', padx=(0, 5), pady=(5, 5))
        self.all_persons = {f'{p.f_name} {p.l_name}': p.id for p in self.get_persons()}
        self.values_combo_dispatcher = list(self.all_persons)
        self.var_combo_dispatcher = tk.StringVar(value=self.values_combo_dispatcher[0])
        self.combo_dispatcher = ttk.Combobox(self.frame_input, values=self.values_combo_dispatcher,
                                             textvariable=self.var_combo_dispatcher, width=46, state='readonly')
        self.combo_dispatcher.grid(row=1, column=1, sticky='w', padx=(5, 0), pady=(5, 5))

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=20, command=self.create)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=20, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(5, 0))

        self.get_persons()

    def create(self):
        team = pm.TeamCreate(name=self.entry_name.get())
        person_id = self.all_persons[self.var_combo_dispatcher.get()]

        response = requests.post(f'{self.parent.host}/admin/team',
                                 json={'team': team.dict(), 'person': {'id': str(person_id)}},
                                 headers={'Authorization': f'Bearer {self.access_token}'})
        data = response.json()
        try:
            team = pm.Team.parse_obj(data)
        except Exception as e:
            tk.messagebox.showerror(parent=self, message=f'{response.text}')
            return
        self.parent.new_team_data = team
        self.destroy()

    def get_persons(self):
        response = requests.get(f'{self.parent.host}/admin/persons',
                                headers={'Authorization': f'Bearer {self.access_token}'})
        all_persons = sorted([pm.Person(**p) for p in response.json()], key=lambda p: p.f_name)
        return all_persons


class ChangeTeam(CommonTopLevel):
    def __init__(self, parent, access_token: str):
        super().__init__(parent)
        self.frame_combo_select.config(padding='20 20 20 20')

        self.access_token = access_token

        self.var_combo_teams = tk.StringVar()
        self.values_combo_teams = {t.name: t for t in
                                   sorted(HelperRequests.get_teams_admin(parent, parent.host, access_token),
                                          key=lambda t: t.name)}
        self.var_combo_teams.set(list(self.values_combo_teams)[0])

        self.lb_combo_teams = tk.Label(self.frame_combo_select, text='Auswahl Team:')
        self.lb_combo_teams.grid(row=0, column=0, sticky='w')
        self.combo_teams = ttk.Combobox(self.frame_combo_select, width=27, values=list(self.values_combo_teams),
                                        textvariable=self.var_combo_teams, state='readonly')
        self.combo_teams.bind('<<ComboboxSelected>>', lambda event: self.autofill())
        self.combo_teams.grid(row=1, column=0, sticky='w')

        self.lb_entry_name = tk.Label(self.frame_input, text='Neuer Teamname:')
        self.lb_entry_name.grid(row=0, column=0, sticky='w')
        self.entry_name = tk.Entry(self.frame_input, width=30)
        self.entry_name.grid(row=1, column=0, sticky='w')

        self.bt_okay = tk.Button(self.frame_buttons, text='okay', width=15, command=self.save)
        self.bt_okay.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(5, 0))

        self.autofill()

    def save(self):
        team = self.values_combo_teams[self.var_combo_teams.get()]

        response = requests.put(f'{self.parent.host}/admin/team',
                                params={'team_id': team.id, 'new_team_name': self.entry_name.get()},
                                headers={'Authorization': f'Bearer {self.access_token}'})
        try:
            updated_team = pm.Team.parse_obj(response.json())
            self.parent.changed_team = updated_team
            self.destroy()
        except:
            tk.messagebox.showerror(parent=self.parent, message=f'{response.text}')

    def autofill(self):
        self.entry_name.delete(0, 'end')
        team = self.values_combo_teams[self.var_combo_teams.get()]
        self.entry_name.insert(0, team.name)


class CreatePlanperiod(tk.Toplevel):
    def __init__(self, parent, host: str, access_token: str):
        super().__init__(parent)
        self.grab_set()
        self.focus_set()
        self.bind('<Escape>', lambda e: self.destroy())

        self.parent = parent
        self.host = host

        self.access_token = access_token

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
        self.lb_calendar_deadline = tk.Label(self.frame_calendar, text='Termin Deadline:')
        self.lb_calendar_deadline.grid(row=0, column=2, sticky='w')
        self.calendar_deadline = tkcalendar.dateentry.DateEntry(self.frame_calendar, locale='de_DE', width=20,
                                                                date_pattern='dd.mm.yyyy')
        self.calendar_deadline.grid(row=1, column=2, padx=(5, 0), sticky='w')

        self.lb_text_notes = tk.Label(self.frame_notes, text='Notitzen:')
        self.lb_text_notes.grid(row=0, column=0, sticky='w')
        self.text_notes = tk.Text(self.frame_notes, width=50, height=10)
        self.text_notes.grid(row=1, column=0, sticky='w')

        self.var_chk_remainder = tk.BooleanVar(value=True)
        self.chk_remainder = tk.Checkbutton(self.frame_notes, text='Email-Remainder schicken',
                                            variable=self.var_chk_remainder)
        self.chk_remainder.grid(row=2, column=0, pady=(10, 0))

        self.bt_ok = tk.Button(self.frame_buttons, text='okay', width=15, command=self.create_period)
        self.bt_ok.grid(row=0, column=0, padx=(0, 10), sticky='e')
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, padx=(10, 0), sticky='w')

        self.get_teams_and_mindates()

    def get_teams_and_mindates(self):
        self.teams = HelperRequests.get_teams_dispatcher(self, self.host, self.access_token)
        self.values_combo_teams = {team.name: team.id for team in self.teams}
        self.var_combo_teams.set(self.teams[0].name)
        self.combo_teams.config(values=list(self.values_combo_teams))

        self.get_last_day_of_existing_planperiods()

    def get_last_day_of_existing_planperiods(self):
        team_id = self.values_combo_teams[self.var_combo_teams.get()]
        response = requests.get(f'{self.host}/dispatcher/pp_last_recent_date',
                                params={'team_id': team_id},
                                headers={'Authorization': f'Bearer {self.access_token}'})
        data = response.json()
        if type(data) == dict and data.get('status_code') == 401:
            tk.messagebox.showerror(parent=self, message='Nicht authorisiert!')
            self.destroy()
        if data:
            last_day: datetime.date = datetime.date(*[int(v) for v in data.split('-')])
            mindate = last_day + datetime.timedelta(days=1)
        else:
            mindate = None
        self.calendar_from.config(mindate=mindate)
        self.calendar_from.set_date(mindate)
        self.calendar_to.config(mindate=mindate)
        self.calendar_to.set_date(mindate)

    def create_period(self):
        team_id = self.values_combo_teams[self.var_combo_teams.get()]
        start: datetime.date = self.calendar_from.get_date()
        end: datetime.date = self.calendar_to.get_date()
        deadline: datetime.date = self.calendar_deadline.get_date()
        notes = self.text_notes.get(1.0, 'end')

        response = requests.post(f'{self.parent.host}/dispatcher/planperiod',
                                 params={'team_id': team_id,
                                         'date_start': start.isoformat(), 'date_end': end.isoformat(),
                                         'deadline': deadline, 'remainder': self.var_chk_remainder.get(),
                                         'notes': notes},
                                 headers={'Authorization': f'Bearer {self.access_token}'})
        self.parent.planperiod = response.json()
        self.destroy()
        tk.messagebox.showinfo(parent=self.parent, message='Planperiode wurde erfolgreich erstellt.')


class DeletePlanperiod(CommonTopLevel):
    def __init__(self, parent, access_token):
        super().__init__(parent)

        self.parent = parent
        self.access_token = access_token

        self.frame_combo_select.config(padding='20 20 20 20')

        self.var_combo_planperiods = tk.StringVar()
        self.var_combo_teams = tk.StringVar()
        self.values_combo_teams = {t.name: str(t.id)
                                   for t in HelperRequests.get_teams_dispatcher(self, parent.host, self.access_token)}
        self.values_combo_planperiods: dict[str, pm.PlanPeriod] = {}

        self.lb_combo_teams = tk.Label(self.frame_combo_select, text='Team')
        self.lb_combo_teams.grid(row=0, column=0, sticky='w')
        self.combo_teams = ttk.Combobox(self.frame_combo_select, values=list(self.values_combo_teams),
                                        textvariable=self.var_combo_teams, state='readonly')
        self.combo_teams.bind('<<ComboboxSelected>>', lambda event: self.autofill())
        self.combo_teams.grid(row=1, column=0, padx=(0, 5))

        self.lb_combo_planperiods = tk.Label(self.frame_combo_select, text='Planperiode:')
        self.lb_combo_planperiods.grid(row=0, column=1, sticky='w', padx=(5, 0))
        self.combo_planperiods = ttk.Combobox(self.frame_combo_select, values=[],
                                              textvariable=self.var_combo_planperiods, state='readonly')
        self.combo_planperiods.grid(row=1, column=1, padx=(5, 0))

        self.bt_ok = tk.Button(self.frame_buttons, text='Löschen', width=15, command=self.delete_planperiod)
        self.bt_ok.grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.bt_cancel = tk.Button(self.frame_buttons, text='cancel', width=15, command=self.destroy)
        self.bt_cancel.grid(row=0, column=1, sticky='w', padx=(5, 0))

    def delete_planperiod(self):
        value_planperiod = self.var_combo_planperiods.get()
        planperiod = self.values_combo_planperiods[value_planperiod]
        if not tk.messagebox.askokcancel(parent=self,
                                         message=f'Achtung!!!\nDie Planperiode {value_planperiod} wird unwiderruflich '
                                                 f'aus der Datenbank gelöscht.\nDas gleiche gilt auch für die '
                                                 f'dazugehörigen Spieloptionen.'
                                                 f'\nDieser Vorgang kann nicht rückgängig gemacht werden.'):
            return
        response = requests.delete(f'{self.parent.host}/dispatcher/planperiod',
                                   params={'planperiod_id': planperiod.id},
                                   headers={'Authorization': f'Bearer {self.access_token}'})
        try:
            deleted_planperiod = pm.PlanPeriod(**response.json())
            tk.messagebox.showinfo(parent=self,
                                   message=f'Die Planperiode "{deleted_planperiod.start}-{deleted_planperiod.end}"'
                                           f'mit allen verbundenen Spieloptionen wurde gelöscht')
            self.destroy()
            return
        except Exception as e:
            tk.messagebox.showinfo(parent=self, message=f'Fehler: {response.json()}\n Exception: {e}')
            self.destroy()

    def autofill(self):
        team_id = self.values_combo_teams[self.var_combo_teams.get()]
        planperiods = HelperRequests.get_planperiods(self, self.parent.host, self.access_token, team_id)
        self.values_combo_planperiods = {f'{pp.start.strftime("%d.%m.%y")} - {pp.end.strftime("%d.%m.%y")}': pp
                                         for pp in planperiods}
        self.combo_planperiods.config(values=list(self.values_combo_planperiods))

        if self.values_combo_planperiods:
            self.var_combo_planperiods.set(list(self.values_combo_planperiods)[0])


class MainMenu(tk.Menu):
    def __init__(self, parent, root: tk.Tk):
        super().__init__(master=parent)
        root.config(menu=self)
        self.file = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Datei', underline=0, menu=self.file)

        self.supervisor = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Supervisor', underline=0, menu=self.supervisor)

        self.admin = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Admin', underline=0, menu=self.admin)

        self.dispatcher = tk.Menu(self, tearoff=0)
        self.add_cascade(label='Dispatcher', underline=0, menu=self.dispatcher)

        self.login = tk.Menu(self, tearoff=0)
        self.add_cascade(label='login', underline=0, command=parent.login)

        self.file.add_command(label='Einstellungen', command=parent.settings)
        self.file.add_command(label='match ids...', command=parent.match_ids)

        self.supervisor.add_command(label='Neues Projekt', command=parent.new_project)

        self.admin.add_command(label='Neues Team...', command=parent.new_team)
        self.admin.add_command(label='Neue/r Mitarbeiter:in...', command=parent.new_person)
        self.admin.add_command(label='Mitarbeiter: Namen ändern...', command=parent.change_person_names)
        self.admin.add_command(label='Mitarbeiter:in einer Position zuweisen...',
                               command=parent.assign_person_to_position)
        self.admin.add_command(label='Team ändern...', command=parent.change_team)
        self.admin.add_command(label='Team löschen...', command=parent.delete_team)
        self.admin.add_command(label='Mitarbeiter löschen...', command=parent.delete_person)
        self.admin.add_command(label='Projektname ändern...', command=parent.change_project_name)
        self.admin.add_command(label='Account löschen...', command=parent.delete_account)

        self.dispatcher.add_command(label='Neue Planperiode...', command=parent.new_planperiod)
        self.dispatcher.add_command(label='Planperiode ändern...', command=parent.change_planperiod)
        self.dispatcher.add_command(label='Planperiode löschen...', command=parent.delete_planperiod)
        self.dispatcher.add_command(label='Spieloptionen...', command=parent.get_avail_days)
        self.dispatcher.add_command(label='Alle Clowns...', command=parent.get_all_actors)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Datenbankverwaltung')
    root.geometry('800x600+00+00')
    mainframe = MainFrame(root)
    mainframe.pack()
    root.menubar = MainMenu(parent=mainframe, root=root)
    root.mainloop()
