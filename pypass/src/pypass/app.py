"""
A Password Manager Written in Python
"""
# Data Structure

# /
#   username
#       .passwords.json

# .passwords.json layout
# {
#   username: user's encrypted password
#   "key": key used for password encryption
#   "servers": {
#       "server_title": {
#           "server_address": The server's IP address,
#           "server_port": The port the server is listening on
#   "data": {
#       service name: {
#           username of service: {
#               "password": the encrypted password,
#               "key": the encryption key
#           }
#       }
#   }
# }

# TODO: Finish the password syncing method, add a way for the user to decide to upload passwords,
#  download passwords, or recursively upload or download. Integrate password requests on server

# Window related imports
from toga.style import Pack

# App related imports
import os.path
import asyncio
import secrets
import textwrap
from .utils import *
import cryptography.fernet
from functools import partial
from cryptography import fernet
from cryptography.fernet import Fernet

# Data migration imports
import httpx
import socket
import psutil

from pprint import pprint as print

if toga.platform.current_platform.lower() == "android" or "window" in toga.platform.current_platform.lower():
    from tatogalib.system.clipboard import Clipboard

else:
    import pyperclip

class PyPass(toga.App):
    # --------------------- App related functions ---------------------#
    async def on_running(self):
        load_env(env_path=os.path.join(self.paths.data, ".env"), env_object=os.environ)
        self.main_fernet: Fernet = await self.get_main_fernet_object()

    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """

        main_box = toga.Box(
            style=Pack(
                direction="column",
                align_items="center",
                justify_content="start"
            )
        )

        if toga.platform.current_platform == "android":
            from org.beeware.android import MainActivity
            self._impl.native = MainActivity.singletonThis

        self.error_title = "Oh No!"
        self.success_title = "Yay!"
        self.confirm_title = "Confirm?"

        self.logged_in_user = None
        self.server_key = None
        self.server = None

        self.backup_words = {
            "A": "afraid",
            "B": "boat",
            "C": "calculation",
            "D": "drive",
            "E": "expense",
            "F": "feed",
            "G": "ground",
            "H": "human",
            "I": "interrupt",
            "J": "juice",
            "K": "keep",
            "L": "live",
            "M": "mother",
            "N": "necessity",
            "O": "observe",
            "P": "pocket",
            "Q": "question",
            "R": "return",
            "S": "strap",
            "T": "truth",
            "U": "university",
            "V": "various",
            "W": "way",
            "X": "xenomorphically",
            "Y": "yard",
            "Z": "zebra",
        }

        server_group = toga.Group(
            text="Server Config",
            order=0
        )

        password_group = toga.Group(
            text="Password Management",
            order=1
        )

        add_new_server_command = toga.Command(
            action=self.collect_server_data,
            text="Add New Server",
            group=server_group,
            order=0
        )

        edit_server_command = toga.Command(
            action=self.collect_server_data,
            text="Edit Server",
            group=server_group,
            order=1
        )

        connect_server_command = toga.Command(
            action=self.collect_server_data,
            text="Connect Server",
            group=server_group,
            order=2
        )

        upload_passwords_command = toga.Command(
            action=self.collect_server_data,
            text="Upload Passwords to Server",
            group=server_group,
            order=3
        )

        download_passwords_command = toga.Command(
            action=self.collect_server_data,
            text="Download Passwords from Server",
            group=server_group,
            order=4
        )

        delete_server_command = toga.Command(
            action=self.collect_server_data,
            text="Delete Server",
            group=server_group,
            order=6
        )

        migrate_passwords_command = toga.Command(
            action=self.migrate_data,
            group=password_group,
            text="Migrate data",
            order=0
        )

        get_app_details_command = toga.Command(
            action=self.get_app_details,
            group=password_group,
            text="Get App Data Folder",
            order=1
        )

        self.selection_style = Pack(
            margin_top=10,
            margin_bottom=10
        )

        self.label_style = Pack(
            margin_top=10,
            margin_bottom=10,
        )

        self.input_style = Pack(
            margin_top=10,
            margin_bottom=10
        )

        self.button_style = Pack(
            margin_top=10,
            margin_bottom=10,
        )

        user_label = toga.Label(
            text="User:",
            style=self.label_style
        )

        self.user_entry = toga.TextInput(
            style=self.input_style
        )

        password_label = toga.Label(
            text="Password:",
            style=self.label_style
        )

        self.password_entry = toga.TextInput(
            style=self.input_style
        )

        login_button = toga.Button(
            text="Login",
            on_press=self.login,
            style=self.button_style
        )

        create_user_button = toga.Button(
            text="Create User",
            on_press=self.create_user,
            style=self.button_style
        )

        delete_user_button = toga.Button(
            text="Delete User",
            on_press=self.delete_user,
            style=Pack(
                margin_top=10,
                margin_bottom=10,
                background_color="red"
            )
        )

        self.a_box = toga.Box(
            style=Pack(
                direction="column",
                align_items="center",
                width=10
            )
        )

        add_to_screen(
            widgets_to_add={
                "user_label": user_label,
                "self.user_entry": self.user_entry,
                "password_label": password_label,
                "self.password_entry": self.password_entry,
                "login_button": login_button,
                "create_user_button": create_user_button,
                "delete_user_button": delete_user_button
            },
            box_to_add_to=self.a_box,
            clear_screen=True
        )

        main_box.add(self.a_box)
        self.commands.clear()

        self.commands.add(edit_server_command)
        self.commands.add(delete_server_command)
        self.commands.add(connect_server_command)
        self.commands.add(add_new_server_command)
        self.commands.add(upload_passwords_command)
        self.commands.add(download_passwords_command)
        self.commands.add(migrate_passwords_command)
        self.commands.add(get_app_details_command)

        self.paths.data.mkdir(parents=True, exist_ok=True)
        self.paths.logs.mkdir(parents=True, exist_ok=True)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    async def recover_key(self, _):
        backup_phrase = self.backup_phrase_entry.value.replace(" ", "").split("/")

        recovered_key = recover_key(backup_phrase=backup_phrase)

        print("The recovered key is: " + recovered_key)

        try:
            Fernet(recovered_key).encrypt(b"text")

        except cryptography.fernet.InvalidToken:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to recover key"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen(logged_in=False)

        else:
            username = self.user_entry.value

            user_data = load_user_data(password_file_path=self.data_file_path)
            user_data["key"] = self.main_fernet.encrypt(recovered_key.encode()).decode()

            with open(self.data_file_path, mode="w") as passwords_file:
                json.dump(user_data, passwords_file, indent=4)

            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Successfully recovered key for user {username}"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen(logged_in=False)

    def return_to_home_screen(self, _=None, logged_in=True):
        if logged_in:
            service_label = toga.Label(
                text="Service: ",
                style=self.label_style
            )

            self.service_entry = toga.TextInput(
                style=self.input_style
            )

            username_label = toga.Label(
                text="Username: ",
                style=self.label_style
            )

            self.username_entry = toga.TextInput(
                style=self.input_style
            )

            password_label = toga.Label(
                text="Password: ",
                style=self.label_style
            )

            self.service_password_entry = toga.TextInput(
                style=self.input_style
            )

            add_password_button = toga.Button(
                text="Add Password",
                on_press=self.add_password,
                style=self.button_style
            )

            generate_password_button = toga.Button(
                text="Generate Password",
                on_press=self.generate_password,
                style=self.button_style
            )

            edit_password_button = toga.Button(
                text="Edit Password",
                on_press=self.edit_password,
                style=self.button_style
            )

            get_password_button = toga.Button(
                text="Get Password",
                on_press=self.get_password,
                style=self.button_style
            )

            delete_service_button = toga.Button(
                text="Delete Service",
                on_press=self.delete_service,
                style=self.button_style
            )

            delete_username_button = toga.Button(
                text="Delete Username",
                on_press=self.delete_username,
                style=self.button_style
            )

            create_backup_phrase_button = toga.Button(
                text="Create backup phrase",
                on_press=self.create_backup_phrase,
                style=self.button_style
            )

            add_to_screen(
                widgets_to_add={
                    "service_label": service_label,
                    "self.service_entry": self.service_entry,
                    "username_label": username_label,
                    "self.username_entry": self.username_entry,
                    "password_label": password_label,
                    "self.service_password_entry": self.service_password_entry,
                    "add_password_button": add_password_button,
                    "generate_password_button": generate_password_button,
                    "edit_password_button": edit_password_button,
                    "get_password_button": get_password_button,
                    "delete_service_button": delete_service_button,
                    "delete_username_button": delete_username_button,
                    "create_backup_phrase_button": create_backup_phrase_button
                },
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        else:
            user_label = toga.Label(
                text="User:",
                style=self.label_style
            )

            self.user_entry = toga.TextInput(
                style=self.input_style
            )

            password_label = toga.Label(
                text="Password:",
                style=self.label_style
            )

            self.password_entry = toga.TextInput(
                style=self.input_style
            )

            login_button = toga.Button(
                text="Login",
                on_press=self.login,
                style=self.button_style
            )

            create_user_button = toga.Button(
                text="Create User",
                on_press=self.create_user,
                style=self.button_style
            )

            delete_user_button = toga.Button(
                text="Delete User",
                on_press=self.delete_user,
                style=Pack(
                    margin_top=10,
                    margin_bottom=10,
                    background_color="red"
                )
            )

            add_to_screen(
                widgets_to_add={
                    "user_label": user_label,
                    "self.user_entry": self.user_entry,
                    "password_label": password_label,
                    "self.password_entry": self.password_entry,
                    "login_button": login_button,
                    "create_user_button": create_user_button,
                    "delete_user_button": delete_user_button
                },
                box_to_add_to=self.a_box,
                clear_screen=True
            )

    async def get_main_fernet_object(self) -> Fernet or None:
        main_key = os.environ.get("MAIN_KEY")
        first_run = os.environ.get("FIRST_RUN")

        if first_run is None:
            first_run = "true"

        if main_key is None and first_run == "false":
            dialog = toga.QuestionDialog(
                title=self.confirm_title,
                message="No main key was found. Do you want to generate a new one? GENERATING A NEW MAIN KEY WILL "
                        "LOSE ALL SAVED PASSWORDS FOR ALL USERS!!!"
            )

            dialog_result = await self.dialog(dialog)

        if first_run == "true" or (main_key is None and dialog_result is True):

            main_key = Fernet.generate_key()
            os.environ["MAIN_KEY"] = main_key.decode()

            with open(os.path.join(self.paths.data, ".env"), mode="w") as env_file:
                json.dump(
                    {
                        "MAIN_KEY": main_key.decode(),
                        "FIRST_RUN": "false"
                    },
                    env_file,
                    indent=4
                )

            for user_folder in os.listdir(self.paths.data):
                if os.path.isdir(user_folder):
                    user_path = os.path.join(self.paths.data, user_folder)

                    os.unlink(
                        os.path.join(
                            user_path,
                            ".passwords.json"
                        )
                    )

                    os.rmdir(user_path)

        main_fernet = Fernet(main_key)
        return main_fernet

    def get_app_details(self, _):
        data_path_label = toga.Label(
            text=f"The data path for PyPass is: {self.paths.data} \nThe Bundle Identifier is: {self.app_id}",
            style=self.label_style
        )

        if self.logged_in_user is None:
            return_to_home_button = toga.Button(
                text="Return to home screen",
                on_press=partial(self.return_to_home_screen, logged_in=False)
            )

        else:
            return_to_home_button = toga.Button(
                text="Return to home screen",
                on_press=self.return_to_home_screen
            )

        return add_to_screen(
            widgets_to_add={
                "data_path_label": data_path_label,
                "return_to_home_button": return_to_home_button
            },
            box_to_add_to=self.a_box,
            clear_screen=True
        )

# --------------------- User related functions ---------------------#

    async def login(self, _):
        username: str = self.user_entry.value
        password: str = self.password_entry.value
        username_path = os.path.join(self.paths.data, username)

        is_valid = await self.validate_values(
            to_validate={
                "username": username,
                "password": password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        if not os.path.exists(username_path):
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"User {username} doesn't exist"
            )

            await self.dialog(
                dialog
            )

            return None

        user_data = load_user_data(password_file_path=os.path.join(username_path, ".passwords.json"))

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to login. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to login. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        try:
            user_password = user_data[username]
            user_key = self.main_fernet.decrypt(user_data["key"].encode())

        except KeyError:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't login to user {username}. No decryption key found"
            )

            return await self.dialog(dialog)

        except fernet.InvalidToken:
            dialog = toga.ConfirmDialog(
                title=self.confirm_title,
                message="An invalid key was saved. Do you want to attempt key recovery? (Requires backup phrase)"
            )

            dialog_result = await self.dialog(dialog)

            if dialog_result:
                backup_phrase_label = toga.Label(
                    text="Please enter your backup phrase below, separating each word with '/ ', or paste in the backup "
                         "phrase that was copied to your clipboard:",
                    style=self.label_style
                )

                self.backup_phrase_entry = toga.TextInput(style=self.input_style)

                recover_backup_phrase_button = toga.Button(
                    text="Recover Key",
                    on_press=self.recover_key,
                    style=self.button_style
                )

                return add_to_screen(
                    widgets_to_add={
                        "backup_phrase_label": backup_phrase_label,
                        "self.backup_phrase_entry": self.backup_phrase_entry,
                        "recover_backup_phrase_button": recover_backup_phrase_button
                    },
                    box_to_add_to=self.a_box,
                    clear_screen=True
                )

        cipher = Fernet(user_key)

        if user_data == {}:
            dialog = toga.ConfirmDialog(
                title=self.confirm_title,
                message="Saved passwords are corrupt. Attempt recovery from server?"
            )

            dialog_result = await self.dialog(dialog)

            if dialog_result:
                server_address_label = toga.Label(
                    text="Server Address:",
                    style=self.label_style
                )

                self.server_address_entry = toga.TextInput(
                    style=self.input_style
                )

                server_port_label = toga.Label(
                    text="Server Port:",
                    style=self.label_style
                )

                self.server_port_entry = toga.TextInput(
                    style=self.input_style
                )

                recover_passwords_button = toga.Button(
                    text="Recover Passwords",
                    on_press=self.download_passwords,
                    style=self.button_style
                )

                add_to_screen(
                    widgets_to_add={
                        "server_address_label": server_address_label,
                        "self.server_address_entry": self.server_address_entry,
                        "server_port_label": server_port_label,
                        "self.server_port_entry": self.server_port_entry,
                        "recover_passwords_button": recover_passwords_button
                    },
                    box_to_add_to=self.a_box,
                    clear_screen=True
                )

        password_correct = check_password(
            entered_password=password,
            saved_password=user_password,
            password_cipher=cipher
        )

        if password_correct == "Correct password entered":
            self.logged_in_user = username
            self.data_file_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

            self.return_to_home_screen()

            return None

        elif password_correct == "Incorrect password entered":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Incorrect password"
            )

            return await self.dialog(dialog)

        else:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Unknown case happened"
            )

            return await self.dialog(dialog)

    async def create_user(self, _):
        user = self.user_entry.value
        password = self.password_entry.value

        self.data_file_path = os.path.join(self.paths.data, user, ".passwords.json")

        is_valid = await self.validate_values(
            {
                "user": user,
                "password": password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        create_user_result = create_new_user(user_data_path=os.path.join(self.paths.data, user), user=user, password=password, main_cipher=self.main_fernet)

        if create_user_result == "User already exists":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"User {user} already exists"
            )

            await self.dialog(dialog)
            return None

        else:
            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Successfully created user {user}"
            )

            await self.dialog(dialog)
            return None

    async def delete_user(self, _):
        user = self.user_entry.value
        password = self.password_entry.value

        user_data = load_user_data(password_file_path=os.path.join(self.paths.data, user, ".passwords.json"))

        if user_data == "":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Cannot delete user. User doesn't exist"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Cannot delete user. Failed to load passwords"
            )

            await self.dialog(dialog)
            return None

        cipher = Fernet(
            self.main_fernet.decrypt(user_data["key"]),
        )

        is_valid = await self.validate_values(
            to_validate={
                "User": user,
                "Password": password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        if password != cipher.decrypt(user_data[user]).decode():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Cannot delete user. Incorrect credentials"
            )

            await self.dialog(dialog)
            return None

        confirm_dialog = toga.ConfirmDialog(
            title=self.confirm_title,
            message=f"Are you really sure you want to delete user {user}?"
        )

        confirm_result = await self.dialog(confirm_dialog)

        if not confirm_result:
            return None

        os.unlink(
            os.path.join(
                self.paths.data,
                user,
                ".passwords.json"
            )
        )

        os.rmdir(
            os.path.join(
                self.paths.data,
                user
            )
        )

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully deleted user {user}"
        )

        await self.dialog(dialog)
        return None

    # --------------------- Password related functions ---------------------#

    async def add_password(self, _):
        service = self.service_entry.value
        username = self.username_entry.value
        password = self.service_password_entry.value

        user_data = load_user_data(self.data_file_path)

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to add password. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to add password. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        if not "data" in user_data.keys():
            user_data["data"] = {}

        password_key = Fernet.generate_key()
        cipher = Fernet(password_key)

        is_valid = await self.validate_values(
            to_validate={
                "service": service,
                "username": username,
                "password": password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )
        if not is_valid:
            return None

        if service in user_data["data"].keys() and username in user_data["data"][service].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't add username {username} to service {service}. Username already exists"
            )

            await self.dialog(dialog)
            return None

        elif service not in user_data["data"].keys():
            user_data["data"][service] = {
                username: {
                    "password": cipher.encrypt(password.encode()).decode(),
                    "key": self.main_fernet.encrypt(password_key).decode()
                }
            }

        elif username not in user_data["data"][service].keys():
            user_data["data"][service][username] = {
                "password": cipher.encrypt(password.encode()).decode(),
                "key": self.main_fernet.encrypt(password_key).decode()
            }

        with open(self.data_file_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        clipboard_result = copy_to_clipboard(password)

        if clipboard_result == "Can't copy to clipboard. Unsupported OS":
            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Successfully added username {username} to service {service}."
            )

        else:
            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Successfully added username {username} to service {service}. \n\nThe Password has been copied to your clipboard"
            )

        await self.dialog(dialog)
        return None

    async def edit_password(self, _):
        new_password = self.service_password_entry.value
        username = self.username_entry.value
        service = self.service_entry.value

        new_key = Fernet.generate_key()
        cipher = Fernet(new_key)

        user_data = load_user_data(password_file_path=self.data_file_path)

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to edit password. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to edit password. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        is_valid = await self.validate_values(
            to_validate={
                "Service": service,
                "Username": username,
                "New Password": new_password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if is_valid is False:
            return None

        if "data" not in user_data.keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't edit password for service {service}. No passwords are saved"
            )

            await self.dialog(dialog)
            return None

        elif service not in user_data["data"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't edit password for service {service}. No such service is saved"
            )

            await self.dialog(dialog)
            return None

        elif username not in user_data["data"][service].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't edit password for service {service} username {username}. No such username is saved"
            )

            await self.dialog(dialog)
            return None

        user_data["data"][service][username]["key"] = self.main_fernet.encrypt(new_key).decode()
        user_data["data"][service][username]["password"] = cipher.encrypt(new_password.encode()).decode()

        with open(self.data_file_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        clipboard_result = copy_to_clipboard(new_password)

        if clipboard_result == "Can't copy to clipboard. Unsupported OS":
            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Successfully edited password for service {service} username {username}."
            )

        else:
            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Successfully edited password for service {service} username {username}\n\nThe new password has also been copied to your clipboard"
            )

        await self.dialog(dialog)
        return None

    async def get_password(self, _):
        service = self.service_entry.value
        username = self.username_entry.value
        user_data = load_user_data(self.data_file_path)

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to get password. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to get password. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        is_valid = await self.validate_values(
            to_validate={
                "service": service,
                "username": username
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        if not "data" in user_data.keys():
            user_data["data"] = {}

        if not service in user_data["data"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Service {service} doesn't exist"
            )

            await self.dialog(dialog)
            return None

        if not username in user_data["data"][service].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Username {username} doesn't exist in service {service}"
            )

            await self.dialog(dialog)
            return None

        encrypted_password: str = user_data["data"][service][username]["password"]
        encryption_key: str = self.main_fernet.decrypt(user_data["data"][service][username]["key"]).decode()

        cipher = Fernet(encryption_key.encode())

        clipboard_result = copy_to_clipboard(cipher.decrypt(encrypted_password).decode())

        if clipboard_result == "Can't copy to clipboard. Unsupported OS":
            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Password for service {service} and username {username} is: \n\n{cipher.decrypt(encrypted_password).decode()}."
            )

        else:
            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Password for service {service} and username {username} is: \n\n{cipher.decrypt(encrypted_password).decode()}. \n\nIt has been copied to your clipboard"
            )

        await self.dialog(dialog)
        return None

    async def delete_username(self, _):
        service = self.service_entry.value
        username = self.username_entry.value

        is_valid = await self.validate_values(
            to_validate={
                "Service": service,
                "Username": username
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        user_data = load_user_data(password_file_path=self.data_file_path)

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to delete username. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to delete username. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        if "data" not in user_data.keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Can't delete password for service {service}. No passwords saved"
            )

            await self.dialog(dialog)
            return None

        elif service not in user_data["data"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Can't delete password for service {service}. No such service saved"
            )

            await self.dialog(dialog)
            return None

        elif username not in user_data["data"][service].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Can't delete password for service {service} username {username}. No such username saved"
            )

            await self.dialog(dialog)
            return None

        del user_data["data"][service][username]

        with open(self.data_file_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully deleted service {service} username {username}"
        )

        return await self.dialog(dialog)

    async def delete_service(self, _):
        service = self.service_entry.value
        user_data = load_user_data(password_file_path=self.data_file_path)

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to delete service. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to delete service. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        is_valid = await self.validate_values(
            to_validate={
                "Service": service,
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        if "data" not in user_data.keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Can't delete password for service {service}. No passwords saved"
            )

            await self.dialog(dialog)
            return None

        elif service not in user_data["data"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Can't delete password for service {service}. No such service saved"
            )

            await self.dialog(dialog)
            return None

        del user_data["data"][service]

        with open(self.data_file_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully deleted service {service}"
        )

        return await self.dialog(dialog)

    async def generate_password(self, _):
        new_password = secrets.token_urlsafe(20)
        self.service_password_entry.value = new_password
        print(self.service_password_entry.value)

    async def create_backup_phrase(self, _):
        user_data = load_user_data(password_file_path=self.data_file_path)

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to create backup phrase. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to create backup phrase. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        user_key: str = self.main_fernet.decrypt(user_data["key"]).decode()
        backup_phrase = []

        print(user_key)

        index = 1
        for character in user_key:
            if character.isnumeric() is True or character == "-" or character == "=" or character == "_":
                string_to_append = character

            elif character.isupper():
                string_to_append = self.backup_words[character.upper()] + "!"

            else:
                string_to_append = self.backup_words[character.upper()]

            if not user_key.index(character) % 3 == 0:
                string_to_append += "    "

            backup_phrase.append(string_to_append)

            index += 1

        phrase_copy_safe = []
        for word in backup_phrase:
            word = word.replace(" ", "")
            word += "/"

            phrase_copy_safe.append(word)
            print(word)

        copy_result = copy_to_clipboard(
            str(phrase_copy_safe).replace("[", "").replace("]", "").replace(",", "").replace("'", ""))
        
        if copy_result == "Can't copy to clipboard. Unsupported OS":
            backup_phrase_label = toga.Label(
                text=textwrap.fill(text=f"Your backup phrase is: \n\n{str(phrase_copy_safe)}"
                                   "\n\nSAVE THIS SOMEWHERE ELSE!!! If your key gets lost, you will not be able to recover it without"
                                   " this backup phrase.".replace("[", "").replace("]", "")
                                   .replace(",", "").replace("'", ""), width=40, drop_whitespace=False),
                style=self.label_style
            )

        else:
            backup_phrase_label = toga.Label(
                text=textwrap.fill(f"Your backup phrase has been copied to your clipboard."
                                   "\n\nSAVE THIS SOMEWHERE ELSE!!! If your key gets lost, you will not be able to recover it without"
                                   " this backup phrase.".replace("[", "").replace("]", "")
                                   .replace(",", "").replace("'", ""), 40, drop_whitespace=False),
                style=self.label_style
            )

        print(self.main_window.size)

        next_button = toga.Button(
            text="Continue to home",
            on_press=self.return_to_home_screen,
            style=self.button_style
        )

        add_to_screen(
            widgets_to_add={
                "backup_phrase_label": backup_phrase_label,
                "next_button": next_button
            },
            box_to_add_to=self.a_box,
            clear_screen=True
        )
        return None

    async def migrate_data(self, _=None, send_data=False, set_up_server=False):
        if send_data:
            user = self.logged_in_user
            main_key = os.environ.get("MAIN_KEY")
            user_data = load_user_data(password_file_path=self.data_file_path)

            if user_data == "Invalid data saved":
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message="Failed to migrate data. Cannot load user data"
                )

                await self.dialog(dialog)
                return None

            elif user_data == "Password file path doesn't exist":
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message="Failed to migrate data. User data file doesn't exist"
                )

                await self.dialog(dialog)
                return None

            user_data = json.dumps(user_data)

            httpx.post(f"http://{self.to_device_address_input.value}:{self.to_device_port_input.value}/{user}/{user_data}/{main_key}")
            httpx.post(f"http://{self.to_device_address_input.value}:{self.to_device_port_input.value}/shutdown")

            dialog = toga.InfoDialog(
                title=self.success_title,
                message="Successfully sent data to receiving device"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        if set_up_server:
            from .migration_server import MigrationServer

            print(send_data)

            server = MigrationServer.set_up_server(
                event_loop=self.loop,
                port=self.server_port_entry.value
            )

            self.server_task = asyncio.create_task(server.serve())

            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Server has been successfully started. Server connection details: \n\nAvailable Addresses: {[psutil.net_if_addrs()[interface][0].address for interface in psutil.net_if_addrs().keys() if psutil.net_if_addrs()[interface][0].address != "127.0.0.1"]} \nPort listening on: {self.server_port_entry.value}"
            )
            print("Showing dialog")

            await self.dialog(dialog)

            print("Waiting for migration to complete")

            while not hasattr(self, "migration_successful"):
                await asyncio.sleep(10)

            await asyncio.to_thread(load_env, env_path=os.path.join(self.paths.data, ".env"), env_object=os.environ)

            dialog = toga.InfoDialog(
                title=self.success_title,
                message="Successfully migrated data"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()
        
        dialog = toga.QuestionDialog(
            title=self.confirm_title,
            message="Do you want to receive or send data? Select 'No' to receive data, and 'Yes' to send data"
        )
        
        dialog_result = await self.dialog(dialog)

        print(dialog_result)
        
        if dialog_result:
            print("Defining widgets")

            to_device_address_label = toga.Label(
                text="Please enter the address of the receiving device",
                style=self.label_style
            )

            self.to_device_address_input = toga.TextInput(style=self.input_style)

            to_device_port_label = toga.Label(
                text="Please enter the port of the receiving device",
                style=self.label_style
            )

            self.to_device_port_input = toga.TextInput(style=self.input_style)

            send_data_button = toga.Button(
                text="Send data to receiving device",
                on_press=partial(self.migrate_data, send_data=True),
                style=self.button_style
            )

            print("Adding widgets to screen")

            add_to_screen(
                widgets_to_add={
                    "to_device_address_label": to_device_address_label,
                    "self.to_device_address_input": self.to_device_address_input,
                    "to_device_port_label": to_device_port_label,
                    "self.to_device_port_input": self.to_device_port_input,
                    "send_data_button": send_data_button
                },
                box_to_add_to=self.a_box,
                clear_screen=True
            )
            
        else:
            dialog = toga.QuestionDialog(
                title=self.confirm_title,
                message="THIS WILL REPLACE ALL PASSWORDS SAVED ON THIS DEVICE. Are you sure you want to continue?"
            )
    
            dialog_result = await self.dialog(dialog)
    
            if dialog_result:
                if set_up_server is False:
                    all_nic_data = psutil.net_if_addrs()
                    available_address = []

                    for nic_name in all_nic_data:
                        nic_data = all_nic_data[nic_name]

                        if nic_data[0].broadcast is not None:
                            available_address.append(nic_data[0].address)

                    select_address_label = toga.Label(
                        text="Please select an address below, or just leave it at the default",
                        style=self.label_style
                    )

                    self.server_address_selection = toga.Selection(
                        items=available_address,
                        style=self.selection_style
                    )

                    server_port_label = toga.Label(
                        text="Please enter a server port below, or leave it at the default",
                        style=self.label_style
                    )

                    self.server_port_entry = toga.TextInput(
                        value="9001",
                        style=self.input_style
                    )

                    start_server_button = toga.Button(
                        text="Start Server",
                        on_press=partial(self.migrate_data, set_up_server=True)
                    )

                    return add_to_screen(
                        widgets_to_add={
                            "select_address_label": select_address_label,
                            "self.server_address_selection": self.server_address_selection,
                            "server_port_label": server_port_label,
                            "self.server_port_entry": self.server_port_entry,
                            "start_server_button": start_server_button
                        },
                        box_to_add_to=self.a_box,
                        clear_screen=True
                    )

            else:
                dialog = toga.InfoDialog(
                    title=self.success_title,
                    message="Data migration has been cancelled"
                )

                return await self.dialog(dialog)

# --------------------- Server related functions ---------------------#

    async def collect_server_data(self, command_called: toga.Command):
        if self.logged_in_user is None:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Please login before configuring servers"
            )

            await self.dialog(dialog)
            return

        print(command_called.text)

        if command_called.text == "Add New Server":
            server_title_label = toga.Label(
                text="Server Title: \n(Can be whatever you want) ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            server_address_label = toga.Label(
                text="Server Address: ",
                style=self.label_style
            )

            self.server_address_entry = toga.TextInput(
                style=self.input_style
            )

            server_port_label = toga.Label(
                text="Server Port: ",
                style=self.label_style
            )

            self.server_port_entry = toga.TextInput(
                value="9000",
                style=self.input_style
            )

            add_server_button = toga.Button(
                text="Add Server",
                on_press=self.add_new_server,
                style=self.button_style
            )

            add_to_screen(
                widgets_to_add={
                    "server_title_label": server_title_label,
                    "self.server_title_entry": self.server_title_entry,
                    "server_address_label": server_address_label,
                    "self.server_address_entry": self.server_address_entry,
                    "server_port_label": server_port_label,
                    "self.server_port_entry": self.server_port_entry,
                    "add_server_button": add_server_button
                },
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        elif command_called.text == "Edit Server":
            server_title_label = toga.Label(
                text="Server Title: \n(Can be whatever you want) ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            server_address_label = toga.Label(
                text="Server Address: ",
                style=self.label_style
            )

            self.server_address_entry = toga.TextInput(
                style=self.input_style
            )

            server_port_label = toga.Label(
                text="Server Port: ",
                style=self.label_style
            )

            self.server_port_entry = toga.TextInput(
                value="9000",
                style=self.input_style
            )

            edit_server_button = toga.Button(
                text="Edit Server",
                on_press=self.edit_server,
                style=self.button_style
            )

            add_to_screen(
                widgets_to_add={
                    "server_title_label": server_title_label,
                    "self.server_title_entry": self.server_title_entry,
                    "server_address_label": server_address_label,
                    "self.server_address_entry": self.server_address_entry,
                    "server_port_label": server_port_label,
                    "self.server_port_entry": self.server_port_entry,
                    "edit_server_button": edit_server_button
                },
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        elif command_called.text == "Delete Server":
            server_title_label = toga.Label(
                text="Server Title: ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            delete_server_button = toga.Button(
                text="Delete Server",
                on_press=self.delete_server,
                style=self.button_style
            )

            add_to_screen(
                widgets_to_add={
                    "server_title_label": server_title_label,
                    "self.server_title_entry": self.server_title_entry,
                    "delete_server_button": delete_server_button
                },
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        if command_called.text == "Upload Passwords to Server":
            server_title_label = toga.Label(
                text="Server Title: ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            sync_passwords_button = toga.Button(
                text="Upload Passwords",
                on_press=self.upload_passwords,
                style=self.button_style
            )

            add_to_screen(
                widgets_to_add={
                    "server_title_label": server_title_label,
                    "self.server_title_entry": self.server_title_entry,
                    "sync_passwords_button": sync_passwords_button
                },
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        elif command_called.text == "Download Passwords from Server":
            server_title_label = toga.Label(
                text="Server Title: ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            download_passwords_button = toga.Button(
                text="Download Passwords",
                on_press=self.download_passwords,
                style=self.button_style
            )

            add_to_screen(
                widgets_to_add={
                    "server_title_label": server_title_label,
                    "self.server_title_entry": self.server_title_entry,
                    "download_passwords_button": download_passwords_button
                },
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        elif command_called.text == "Connect Server":
            server_title_label = toga.Label(
                text="Server Title: ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            connect_server_button = toga.Button(
                text="Connect to Server",
                on_press=self.connect_to_server,
                style=self.button_style
            )

            add_to_screen(
                widgets_to_add={
                    "server_title_label": server_title_label,
                    "self.server_title_entry": self.server_title_entry,
                    "connect_server_button": connect_server_button
                },
                box_to_add_to=self.a_box,
                clear_screen=True
            )

    async def add_new_server(self, _):
        server_title = self.server_title_entry.value
        server_address = self.server_address_entry.value
        server_port = self.server_port_entry.value

        user_data = load_user_data(password_file_path=self.data_file_path)
        user_data_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to add new server. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to add new server. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        is_valid = await self.validate_values(
            to_validate={
                "Server Title": server_title,
                "Server Address": server_address,
                "Server Port": server_port
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        if "servers" not in user_data.keys():
            user_data["servers"] = {}

        for server in user_data["servers"].keys():
            if server_address in user_data["servers"][server].keys():
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message=f"Couldn't add new server. Server with address of {server_address} is already saved"
                )

                await self.dialog(dialog)
                return None

        if server_title in user_data["servers"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't add new server. Server titled {server_title} already exists"
            )

            await self.dialog(dialog)
            return None

        user_data["servers"][server_title] = {
            "server_address": server_address,
            "server_port": server_port
        }

        with open(user_data_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully added new server titled {server_title}"
        )

        await self.dialog(dialog)

        return self.return_to_home_screen()

    async def edit_server(self, _):
        server_title = self.server_title_entry.value
        server_address = self.server_address_entry.value
        server_port = self.server_port_entry.value

        user_data = load_user_data(password_file_path=self.data_file_path)
        data_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to edit server. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to edit server. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        is_valid = await self.validate_values(
            to_validate={
                "Server Title": server_title,
                "Server Address": server_address,
                "Server Port": server_port
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        server_exists = self.check_for_server(server_title)

        if not server_exists:
            return None

        del user_data["servers"][server_title]

        user_data["servers"][server_title] = {
            "server_address": server_address,
            "server_port": server_port
        }

        with open(data_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully edited server {server_title}"
        )

        await self.dialog(dialog)

        return self.return_to_home_screen()

    async def delete_server(self, _):
        server_title = self.server_title_entry.value

        user_data = load_user_data(password_file_path=self.data_file_path)
        data_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to delete server. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to delete server. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        is_valid = await self.validate_values(
            to_validate={
                "Server title": server_title
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        server_exists = await self.check_for_server(server_title)

        if not server_exists:
            return None

        del user_data["servers"][server_title]

        with open(data_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully deleted server {server_title}"
        )

        await self.dialog(dialog)
        return self.return_to_home_screen()

    async def upload_passwords(self, _):
        if self.server is None:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="No server is connected. Please connect to a server, and try again"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        server_title = self.server_title_entry.value

        user_data = load_user_data(password_file_path=self.data_file_path)

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to upload passwords to server. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to upload passwords to server. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        is_valid = await self.validate_values(
            to_validate={
                "Server Title": server_title
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return self.return_to_home_screen()

        server_exists = await self.check_for_server(server_title)

        if not server_exists:
            return self.return_to_home_screen()

        if not "data" in user_data.keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Can't upload passwords. No passwords are saved"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        try:
            for_server = {}
            server_cipher = Fernet(self.server_key)

        except ValueError:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="The server sent an invalid key. Please restart the app, and try again"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        for service in user_data["data"].keys():
            for username in user_data["data"][service].keys():
                encrypted_password = user_data["data"][service][username]["password"]
                encryption_key = user_data["data"][service][username]["key"]
                print(encryption_key)
                cipher = Fernet(self.main_fernet.decrypt(encryption_key))

                if service not in for_server.keys():
                    for_server[service] = {
                        username: {
                            "password": cipher.decrypt(encrypted_password).decode(),
                            "key": self.server_key.decode()
                        }
                    }

                else:
                    for_server[service][username] = {
                        "password": cipher.decrypt(encrypted_password).decode(),
                        "key": self.server_key.decode()
                    }

        encrypted_for_server_string: bytes = server_cipher.encrypt(
            self.main_fernet.encrypt(
                json.dumps(for_server).encode()
            )
        )

        print(f"Encrypted string is: {encrypted_for_server_string}")
        await asyncio.to_thread(self.server.sendall, encrypted_for_server_string)
        print("Sent data")

        await asyncio.to_thread(self.server.sendall, b"DONE")

        confirm_dialog = toga.QuestionDialog(
            title=self.confirm_title,
            message="Do you want to recursively update data on server (Doesn't replace deleted passwords)?"
        )

        update_recursively = await self.dialog(confirm_dialog)

        print(f"Update recursively is: {update_recursively}")

        if update_recursively:
            await asyncio.to_thread(self.server.sendall, server_cipher.encrypt(self.main_fernet.encrypt(b"RECURSIVE")))
            print("Sent recursive command to server")

        else:
            await asyncio.to_thread(self.server.sendall, server_cipher.encrypt(self.main_fernet.encrypt(b"REPLACE")))

        self.server.sendall(server_cipher.encrypt(self.main_fernet.encrypt(b"DONE")))
        print("Sent done message to server")

        message_from_server = await asyncio.to_thread(self.server.recv, 1024)

        if message_from_server.decode() == "Successfully updated data":
            dialog = toga.InfoDialog(
                title=self.success_title,
                message="Successfully updated data"
            )

            await self.dialog(dialog)

        else:
            print(message_from_server)

        await asyncio.to_thread(self.server.close)
        self.server = None

        return self.return_to_home_screen()

    async def download_passwords(self, button_called: toga.Button):
        if button_called.text == "Recover Passwords":
            server_address = self.server_address_entry.value
            server_port = int(self.server_port_entry.value)

            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.connect((server_address, server_port))

            except ConnectionRefusedError:
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message=f"Couldn't connect to server. Connection to server was refused. Please make sure the server address is correct, and listening on port {server_port}"
                )

                await self.dialog(dialog)
                return self.return_to_home_screen()

            await asyncio.to_thread(self.server.sendall, self.user_entry.value.encode())
            encrypted_server_key = await asyncio.to_thread(self.server.recv, 1024)

            try:
                self.server_key = self.main_fernet.decrypt(encrypted_server_key)

            except ValueError:
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message="The server sent an invalid key. Please restart the app, and try again"
                )

                await self.dialog(dialog)
                return self.return_to_home_screen()

        if self.server is None:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="No server is connected. Please connect to a server, and try again"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        if not button_called.text == "Recover Passwords":
            server_title = self.server_title_entry.value

            data_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

        else:
            data_path = os.path.join(self.paths.data, self.user_entry.value, ".passwords.json")

        if not button_called.text == "Recover Passwords":
            is_valid = await self.validate_values(
                to_validate={
                    "Server Title": server_title
                },
                message_for_dialog="<value> cannot be empty",
                inverse_check=True
            )

            if not is_valid:
                print("Invalid values")
                return None

            server_exists = await self.check_for_server(server_title)

            if not server_exists:
                return None

        print("Sending download command")
        self.server.sendall(
            Fernet(self.server_key).encrypt(self.main_fernet.encrypt(b"DOWNLOAD_DATA"))
        )

        print("Sent download command to server, await response")

        downloaded_user_data_str: str = receive_all(
            server_key=self.server_key,
            main_cipher=self.main_fernet,
            server_connection=self.server,
        )

        print("Finished calling receive_all")

        if downloaded_user_data_str.startswith("Failed to download passwords. "):
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Failed to download password from server. Reason: {downloaded_user_data_str.replace('Failed to download passwords. ', '')}"
            )

            self.return_to_home_screen()
            return await self.dialog(dialog)

        await asyncio.to_thread(self.server.close)
        self.server = None

        print("Received response")

        if not button_called.text == "Recover Passwords":
            dialog = toga.QuestionDialog(
                title=self.confirm_title,
                message=f"Are you sure you want to download all passwords from the server titled {server_title}? \n\n"
                        "NOTE: This will overwrite all your existing passwords. "
                        "Any passwords that aren't saved to the server, will be lost"
            )

            dialog_result = await self.dialog(dialog)

        else:
            dialog_result = True

        if dialog_result:
            downloaded_server_data = json_repair.loads(downloaded_user_data_str)

            for downloaded_service in downloaded_server_data.keys():
                for downloaded_username in downloaded_server_data[downloaded_service].keys():
                    password = downloaded_server_data[downloaded_service][downloaded_username]["password"]
                    key = downloaded_server_data[downloaded_service][downloaded_username]["key"]
                    cipher = Fernet(key.encode())

                    downloaded_server_data[downloaded_service][downloaded_username] = {
                        "password": cipher.encrypt(password.encode()).decode(),
                        "key": self.main_fernet.encrypt(key.encode()).decode()
                    }

            user = self.user_entry.value
            password = self.password_entry.value
            encryption_key = Fernet.generate_key()

            user_data = load_user_data(password_file_path=self.data_file_path)

            if user_data == "Invalid data saved":
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message="Failed to download passwords from server. Cannot load user data"
                )

                await self.dialog(dialog)
                return None

            elif user_data == "Password file path doesn't exist":
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message="Failed to download passwords from server. User data file doesn't exist"
                )

                await self.dialog(dialog)
                return None

            downloaded_user_data = {
                user: Fernet(encryption_key).encrypt(password.encode()).decode(),
                "key": self.main_fernet.encrypt(encryption_key).decode(),
                "data": downloaded_server_data,
                "servers": user_data["servers"]
            }

            with open(data_path, mode="w") as data_file:
                json.dump(downloaded_user_data, data_file, indent=4)

            if not button_called.text == "Recover Passwords":
                dialog = toga.InfoDialog(
                    title=self.success_title,
                    message=f"Successfully downloaded passwords from server titled {server_title}"
                )

                await self.dialog(dialog)

            else:
                dialog = toga.InfoDialog(
                    title=self.success_title,
                    message="Successfully recovered data"
                )

                await self.dialog(dialog)

        return self.return_to_home_screen()

    async def connect_to_server(self, _):
        server_title = self.server_title_entry.value
        user_data = load_user_data(password_file_path=self.data_file_path)

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to connect to server. Cannot load user data"
            )

            await self.dialog(dialog)
            return None

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to connect to server. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return None

        if self.server is not None:
            await asyncio.to_thread(self.server.close)

        server_exists = await self.check_for_server(server_title)

        print(f"Server exists: {server_exists}")

        if not server_exists:
            return None

        server_data = user_data["servers"][server_title]
        print("Retrieved server data")

        try:
            print("Connecting to server")
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect((server_data["server_address"], int(server_data["server_port"])))

            print("Was able to connect to server`")

        except ConnectionRefusedError:
            print("Connection was refused")
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't connect to server titled {server_title}. Connection was refused. \n "
                        f"Please ensure the server is running and listening on port {server_data['server_port']}"
            )

            return await self.dialog(dialog)

        self.server.sendall(self.logged_in_user.encode())
        await asyncio.to_thread(self.server.sendall, os.environ["MAIN_KEY"].encode())
        print("Sent logged in user and main key")

        try:
            encrypted_server_key = await asyncio.to_thread(self.server.recv, 1024)
            self.server_key = self.main_fernet.decrypt(encrypted_server_key)

        except ValueError:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="The server sent an invalid key. Please restart the app, and try again"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully connected to server titled {server_title}"
        )

        self.return_to_home_screen()
        return await self.dialog(dialog)

    async def check_for_server(self, server_title: str) -> bool:
        user_data = load_user_data(password_file_path=self.data_file_path)

        if user_data == "Invalid data saved":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to check for server. Cannot load user data"
            )

            await self.dialog(dialog)
            return False

        elif user_data == "Password file path doesn't exist":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to check for server. User data file doesn't exist"
            )

            await self.dialog(dialog)
            return False

        if "servers" not in user_data.keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="No servers are saved. Please save a server, then try again"
            )

            await self.dialog(dialog)
            self.return_to_home_screen()
            return False

        if server_title not in user_data["servers"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"No server titled {server_title} is saved"
            )

            await self.dialog(dialog)
            return False

        return True

    # --------------------- Utility related functions ---------------------#

    async def validate_values(self, to_validate: dict, message_for_dialog: str or None, expected_value: str = "",
                              dialog_to_raise=None, inverse_check: bool = False):
        """
        A function to validate a list of variables

        to_validate: dict    The list of variables to validate. The key will be used to replace <value> in
        message_for_dialog. The value will be what is checked for validity

        message_for_dialog: str or None    The message used when a ErrorDialog is automatically generated. If
        dialog_to_raise is not None, then this is not required. Wherever <value> is put in message_for_dialog,
        it will be replaced with the value of to_validate that is currently being validated

        expected_value: str = ""    The value that all values of to_validate will be checked for

        dialog_to_raise = None    The dialog that will be raised if any value of to_validate isn't valid. If None,
        message_for_dialog is required, and an ErrorDialog will automatically be generated.

        inverse_check: bool = False    If True, a dialog will only be created if any value of to_validate equals expected_value
        """

        for variable in to_validate.keys():
            variable_value = to_validate.get(variable)

            if dialog_to_raise is None:
                dialog_to_raise = toga.ErrorDialog(
                    title=self.error_title,
                    message=message_for_dialog.replace("<value>", variable)
                )
            if inverse_check is False and variable_value != expected_value:
                await self.dialog(dialog_to_raise)

                return False

            if inverse_check is True and variable_value == expected_value:
                await self.dialog(dialog_to_raise)

                return False

            if message_for_dialog is not None:
                dialog_to_raise = None

        return True

def main():
    return PyPass()