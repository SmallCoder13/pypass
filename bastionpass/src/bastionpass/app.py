"""
A cross-platform password manager written in python
"""
import json

import json_repair
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

# Window related imports
import toga
from toga.style import Pack

# App related imports
import random
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
# import httpx
import psutil
import multiprocessing

from pprint import pprint as print

if toga.platform.current_platform.lower() == "android" or "window" in toga.platform.current_platform.lower():
    from tatogalib.system.clipboard import Clipboard

else:
    import pyperclip

# Transfer migration ability from migration server to background server
# Command successfully sent to server, have to add handling for send command

class BastionPass(toga.App):
    async def on_running(self):
        load_env(env_path=Path(self.paths.data, ".env"), env_object=os.environ)

        if os.environ.get("PORT") is None:
            os.environ["PORT"] = "9000"

            if Path(self.paths.data, ".env").exists():
                env_data = json_repair.from_file(Path(self.paths.data, ".env"))

            else:
                env_data = {
                    "PORT": "9000"
                }

            with open(Path(self.paths.data, ".env"), mode="w") as env_file:
                json.dump(env_data, env_file)

        if toga.platform.current_platform.lower() == "android":
            self.main_fernet = None

        else:
            self.main_fernet: Fernet = Fernet(get_main_key())

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

        password_group = toga.Group(
            text="Password Management",
            order=1
        )

        send_passwords_command = toga.Command(
            action=self.send_data,
            group=password_group,
            text="Send data to new device",
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
            widgets_to_add=(
                user_label,
                self.user_entry,
                password_label,
                self.password_entry,
                login_button,
                create_user_button,
                delete_user_button
            ),
            box_to_add_to=self.a_box,
            clear_screen=True
        )

        main_box.add(self.a_box)

        self.commands.clear()
        self.commands.add(send_passwords_command)
        self.commands.add(get_app_details_command)

        self.paths.data.mkdir(parents=True, exist_ok=True)
        self.paths.logs.mkdir(parents=True, exist_ok=True)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    async def recover_key(self, _):
        if toga.platform.current_platform != "android":
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

        else:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Key recovery is not available on android"
            )

            await self.dialog(dialog)
            return None

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

            home_widgets = (
                service_label,
                self.service_entry,
                username_label,
                self.username_entry,
                password_label,
                self.service_password_entry,
                add_password_button,
                generate_password_button,
                edit_password_button,
                get_password_button,
                delete_service_button,
                delete_username_button
            )

            add_to_screen(
                widgets_to_add=home_widgets,
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
                widgets_to_add=(
                    user_label,
                    self.user_entry,
                    password_label,
                    self.password_entry,
                    login_button,
                    create_user_button,
                    delete_user_button
                ),
                box_to_add_to=self.a_box,
                clear_screen=True
            )

    def get_app_details(self, _):
        data_path_label = toga.Label(
            text=f"The data path for Bastion Pass is: {self.paths.data} \nThe Bundle Identifier is: {self.app_id}",
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
            widgets_to_add=(
                data_path_label,
                return_to_home_button
            ),
            box_to_add_to=self.a_box,
            clear_screen=True
        )

    # --------------------- User related functions ---------------------#

    async def login(self, _):
        username: str = self.user_entry.value
        password: str = self.password_entry.value
        username_path = Path(self.paths.data, username)

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

        user_data = load_user_data(password_file_path=Path(username_path, ".passwords.json"))

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

            if self.main_fernet is None and toga.platform.current_platform.lower() == "android":
                pass

            elif self.main_fernet is None and toga.platform.current_platform.lower() != "android":
                raise KeyError

            else:
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
                    widgets_to_add=(
                        backup_phrase_label,
                        self.backup_phrase_entry,
                        recover_backup_phrase_button
                    ),
                    box_to_add_to=self.a_box,
                    clear_screen=True
                )

        if toga.platform.current_platform.lower() == "android":
            cipher = None

        else:
            cipher = Fernet(user_key)

        if user_data == {}:
            dialog = toga.ConfirmDialog(
                title=self.confirm_title,
                message="Saved passwords are corrupt. Attempt recovery from different device?"
            )

            dialog_result = await self.dialog(dialog)

            if dialog_result:
                pass
                # TODO: Implement data receiving from different device

        if toga.platform.current_platform.lower() == "android":
            print("Running data decrypt for android")
            user_data = load_user_data(Path(self.paths.data, username, ".passwords.json"))

            decrypted_key = decrypt_data(data_to_decrypt=user_data["key"], iv=user_data["iv"].encode())

            print(decrypted_key)

            password_correct = check_password(
                entered_password=password,
                saved_password=user_password,
                password_cipher=Fernet(decrypted_key)
            )

        else:
            print("Running data decryption normally")
            password_correct = check_password(
                entered_password=password,
                saved_password=user_password,
                password_cipher=cipher
            )

        if password_correct == "Correct password entered":
            from .background_server import BackgroundServer

            app_side, server_side = multiprocessing.Pipe(duplex=True)

            self.app_pipe = app_side
            self.logged_in_user = username
            self.data_file_path = Path(self.paths.data, self.logged_in_user, ".passwords.json")

            print("Starting background server")

            server_process = multiprocessing.Process(
                target=BackgroundServer,
                kwargs={
                    "port": os.environ["PORT"],
                    "username": self.logged_in_user,
                    "data_path": self.data_file_path,
                    "comms_pipe": self.app_pipe
                }
            )
            server_process.start()

            print(f"Started new process. PID is: {server_process.pid}")

            return self.return_to_home_screen()

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

        self.data_file_path = Path(self.paths.data, user, ".passwords.json")

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

        if toga.platform.current_platform.lower() == "android":
            create_user_result = create_new_user(user_data_path=Path(self.paths.data, user), user=user,
                                                 password=password, main_cipher="AndroidKeyStore")

        else:
            create_user_result = create_new_user(user_data_path=Path(self.paths.data, user), user=user,
                                                 password=password, main_cipher=self.main_fernet)

        if create_user_result == "User already exists":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"User {user} already exists"
            )

            await self.dialog(dialog)
            return None

        elif create_user_result == "Couldn't encrypt password":
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to encrypt supplied password"
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

        user_data = load_user_data(password_file_path=Path(self.paths.data, user, ".passwords.json"))

        if user_data == "" or user_data == "Password file path doesn't exist":
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

        if toga.platform.current_platform.lower() == "android":
            print(user_data)

            encrypted_key = user_data["key"]
            encryption_iv = user_data["iv"]

            cipher = Fernet(decrypt_data(data_to_decrypt=encrypted_key, iv=encryption_iv))

        else:
            cipher = Fernet(self.main_fernet.decrypt(user_data["key"]))

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

        Path(self.paths.data, user, ".passwords.json").unlink(missing_ok=True)
        Path(self.paths.data, user).rmdir()

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully deleted user {user}"
        )

        await self.dialog(dialog)
        return None

    # --------------------- Password related functions --------------------- #

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
            # Use AndroidKeyStore on android. On other platforms, use Fernet
            if toga.platform.current_platform.lower() == "android":
                key_encryption = encrypt_data(data_to_encrypt=password_key)

                user_data["data"][service] = {
                    username: {
                        "password": cipher.encrypt(password.encode()).decode(),
                        "key": key_encryption["encrypted_data"],
                        "iv": key_encryption["iv_used"]
                    }
                }

            else:
                user_data["data"][service] = {
                    username: {
                        "password": cipher.encrypt(password.encode()).decode(),
                        "key": self.main_fernet.encrypt(password_key).decode()
                    }
                }

        elif username not in user_data["data"][service].keys():
            if toga.platform.current_platform.lower() == "android":
                key_encryption = encrypt_data(data_to_encrypt=password_key)

                user_data["data"][service][username] = {
                    "password": Fernet(password_key).encrypt(password.encode()).decode(),
                    "key": key_encryption["encrypted_data"],
                    "iv": key_encryption["iv_used"]
                }

            else:
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

        if toga.platform.current_platform.lower() == "android":
            key_encryption = encrypt_data(data_to_encrypt=new_key)

            user_data["data"][service][username] = {
                "password": Fernet(new_key).encrypt(new_password.encode()).decode(),
                "key": key_encryption["encrypted_data"],
                "iv": key_encryption["iv_used"]
            }

        else:
            user_data["data"][service][username] = {
                "password": cipher.encrypt(new_password.encode()).decode(),
                "key": self.main_fernet.encrypt(new_key).decode()
            }

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
        encrypted_key: bytes = user_data["data"][service][username]["key"].encode()

        if toga.platform.current_platform.lower() == "android":
            encryption_iv: str = user_data["data"][service][username]["iv"]
            encryption_key = decrypt_data(data_to_decrypt=encrypted_key, iv=encryption_iv)

        else:
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
            widgets_to_add=(
                backup_phrase_label,
                next_button
            ),
            box_to_add_to=self.a_box,
            clear_screen=True
        )
        return None

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

    # --------------------- Migration related functions --------------------- #

    async def send_data(self, _, ready_to_send: bool = False):
        if ready_to_send is False:
            self.addresses_selection = toga.Selection(
                items=[psutil.net_if_addrs()[interface][0].address for interface in psutil.net_if_addrs() if psutil.net_if_addrs()[interface][0].address != "127.0.0.1"],
                style=self.selection_style
            )

            submit_address_button = toga.Button(
                style=self.button_style,
                text="Submit address",
                on_press = partial(self.send_data, ready_to_send=True)
            )

            add_to_screen(
                widgets_to_add=(
                    self.addresses_selection,
                    submit_address_button
                ),
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        else:
            await asyncio.to_thread(
                self.app_pipe.send,
                f"COMMAND SEND ADDRESS {self.addresses_selection.value} PORT {os.environ['PORT']} PATH {self.data_file_path}"
            )

            await asyncio.to_thread(
                self.app_pipe.send,
                "DONE"
            )

            # self.app_pipe.send(f"COMMAND SEND ADDRESS {self.addresses_selection.value} PORT {os.environ['PORT']} PATH {self.data_file_path}"),
            # self.app_pipe.send("DONE")

            print(f"COMMAND SEND ADDRESS {self.addresses_selection.value} PORT {os.environ['PORT']}")


def main():
    return BastionPass()
