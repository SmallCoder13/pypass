"""
A cross-platform password manager written in python
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

# Window related imports
import toga
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
from queue import Queue, Empty, Full
from cryptography.fernet import Fernet

# Data migration imports
# import httpx
import psutil
# import multiprocessing

from pprint import pprint as print

if toga.platform.current_platform.lower() == "android" or "window" in toga.platform.current_platform.lower():
    from tatogalib.system.clipboard import Clipboard

else:
    import pyperclip

# Transfer migration ability from migration server to background server
# Command successfully sent to server and send functionality working. Work on adding Connection Refused handling

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

        self.loop.create_task(self.server_message_listener())

    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """

        self.error_title = "Oh No!"
        self.success_title = "Yay!"
        self.warning_title = "Ok..."
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
            margin=10,
            text_align="center"
        )

        self.label_style = Pack(
            margin=10,
            text_align="center"
        )

        self.input_style = Pack(
            margin=10,
            text_align="center"
        )

        self.button_style = Pack(
            margin=10,
            text_align="center"
        )

        self.a_box = toga.Box(
            style=Pack(
                flex=1,
                direction="column",
                align_items="center",
                justify_content="center"
            )
        )

        self.return_to_home_screen(logged_in=False)

        main_scroll = toga.ScrollContainer(content=self.a_box)

        self.commands.clear()
        self.commands.add(send_passwords_command)
        self.commands.add(get_app_details_command)

        self.paths.data.mkdir(parents=True, exist_ok=True)
        self.paths.logs.mkdir(parents=True, exist_ok=True)
        # multiprocessing.set_start_method("spawn")

        self.main_window = toga.MainWindow(
            title=self.formal_name,
            on_close=self.on_close_handler
        )

        self.main_window.content = main_scroll
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

            import_passwords_from_file = toga.Button(
                text="Import Password from File",
                on_press=self.import_from_file,
                style=self.button_style
            )

            create_backup_phrase_button = toga.Button(
                text="Create backup phrase",
                on_press=self.create_backup_phrase,
                style=self.button_style
            )

            if toga.platform.current_platform == "android":
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

            else:
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
                    delete_username_button,
                    create_backup_phrase_button,
                    import_passwords_from_file
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
                    margin=10,
                    text_align="center",
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
                style=self.button_style,
                text="Return to home screen",
                on_press=partial(self.return_to_home_screen, logged_in=False)
            )

        else:
            return_to_home_button = toga.Button(
                style=self.button_style,
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

        if not Path(username_path).exists():
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

            self.server_queue = Queue()
            self.app_queue = Queue()
            # app_side, server_side = multiprocessing.Pipe(duplex=True)

            # self.server_loop = self.loop.create_task(
            #     asyncio.new_event_loop().run_until_complete()
            # )

            self.logged_in_user = username
            self.data_file_path = Path(self.paths.data, self.logged_in_user, ".passwords.json")

            print("Setting up/Starting background server")

            self.loop.create_task(
                asyncio.to_thread(
                    BackgroundServer,
                    app_queue=self.app_queue,
                    port=int(os.environ["PORT"]),
                    username=self.logged_in_user,
                    data_path=self.data_file_path,
                    server_queue=self.server_queue,
                )
            )

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
        # user_data = load_user_data(password_file_path=self.data_file_path)
        #
        # if user_data == "Invalid data saved":
        #     dialog = toga.ErrorDialog(
        #         title=self.error_title,
        #         message="Failed to create backup phrase. Cannot load user data"
        #     )
        #
        #     await self.dialog(dialog)
        #     return None
        #
        # elif user_data == "Password file path doesn't exist":
        #     dialog = toga.ErrorDialog(
        #         title=self.error_title,
        #         message="Failed to create backup phrase. User data file doesn't exist"
        #     )
        #
        #     await self.dialog(dialog)
        #     return None

        try:
            dialog = toga.SaveFileDialog(
                title="Main key backup phrase save path",
                suggested_filename="bastionpass_backup_phrase.json",
                file_types=["json"]
            )

            file_path = await self.dialog(dialog)

        except NotImplemented:
            able_to_save_to_file: bool = False

        else:
            able_to_save_to_file: bool = True

        if file_path is None:
            dialog = toga.InfoDialog(
                title=self.success_title,
                message="Canceled backup phrase creation"
            )

            return await self.dialog(dialog)

        main_key: str = get_main_key()
        user_key: str = decrypt_data(
            load_user_data(
                self.data_file_path
            )["key"].encode()
        )

        print(main_key)

        main_backup_phrase = create_backup_phrase(
            phrase=main_key,
            wordlist=self.backup_words
        )

        user_backup_phrase = create_backup_phrase(
            phrase=user_key,
            wordlist=self.backup_words
        )

        phrase_copy_safe = []
        for word in main_backup_phrase:
            word = word.replace(" ", "")
            word += "/"

            phrase_copy_safe.append(word)
            print(word)

        if able_to_save_to_file is False:
            copy_result = copy_to_clipboard(
                str(phrase_copy_safe).replace("[", "").replace("]", "").replace(",", "").replace("'", ""))

        if able_to_save_to_file is False and copy_result == "Can't copy to clipboard. Unsupported OS":
            backup_phrase_label = toga.Label(
                text=textwrap.fill(text=f"Your backup phrase is: \n\n{str(phrase_copy_safe)}"
                                        "\n\nSAVE THIS SOMEWHERE ELSE!!! If your key gets lost, you will not be able to recover it without"
                                        " this backup phrase.".replace("[", "").replace("]", "")
                                   .replace(",", "").replace("'", ""), width=40, drop_whitespace=False),
                style=self.label_style
            )

        elif able_to_save_to_file is False and copy_result == "Successfully copied to clipboard":
            backup_phrase_label = toga.Label(
                text=textwrap.fill(f"Your backup phrase has been copied to your clipboard."
                                   "\n\nSAVE THIS SOMEWHERE ELSE!!! If your key gets lost, you will not be able to recover it without"
                                   " this backup phrase.".replace("[", "").replace("]", "")
                                   .replace(",", "").replace("'", ""), 40, drop_whitespace=False),
                style=self.label_style
            )

        elif able_to_save_to_file:
            if Path(file_path).exists():
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message="Unable to save backup phrase to file. Selected path already exists"
                )

                return await self.dialog(dialog)

            writable_backup_phrase = {
                "main_key": tuple(main_backup_phrase),
                "user_key": tuple(user_backup_phrase)
            }

            with open(Path(file_path), mode="w") as back_file:
                json.dump(writable_backup_phrase, back_file, indent=4)

        print(self.main_window.size)

        if able_to_save_to_file is False:
            next_button = toga.Button(
                text="Continue to home",
                on_press=self.return_to_home_screen,
                style=self.button_style
            )

            return add_to_screen(
                widgets_to_add=(
                    backup_phrase_label,
                    next_button
                ),
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        else:
            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Successfully created backup phrase. It has been saved to this file: \n\n{file_path}"
            )

            return await self.dialog(dialog)

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

    async def import_from_file(self, _=None, show_path_dialog: bool=False, save_passwords: bool=False):
        if show_path_dialog:

            file_path_dialog = toga.OpenFileDialog(
                title="Select file to import passwords from",
                file_types=["txt"]
            )

            file_path: Path = await self.dialog(file_path_dialog)

            imported_data = import_from_file(
                path=file_path,
                file_pattern=self.data_pattern_input.value.split("\n")
            )

            if imported_data == "Path nonexistent":
                await self.dialog(
                    toga.ErrorDialog(
                        title=self.error_title,
                        message="Unable to import password from file. Provided file doesn't exist"
                    )
                )

            imported_data_label = toga.Label(
                text="The imported data is listed below. Does everything look right?",
                style=self.label_style
            )

            self.imported_data_input = toga.MultilineTextInput(
                style=self.input_style
            )

            for service in imported_data.keys():
                for username in imported_data[service].keys():
                    self.imported_data_input.value += f"Service: {service} \nUsername: {username} \nPassword: {imported_data[service][username]} \n\n"

            conflicting_usernames_box = toga.Box(
                style=Pack(
                    direction="row",
                    justify_content="center"
                )
            )

            self.old_alignment = self.a_box.style.align_items
            self.a_box.style.align_items = "center"

            keep_current_username_label = toga.Label(
                text="Keep any conflicting usernames same as already saved"
            )

            self.conflicting_username_toggle = toga.Switch(
                text=""
            )

            replace_with_imported_username_label = toga.Label(
                text="Replace any conflicting usernames with imported username"
            )

            save_passwords_button = toga.Button(
                text="Save imported passwords",
                on_press=partial(
                    self.import_from_file,
                    save_passwords=True
                )
            )

            add_to_screen(
                widgets_to_add=(
                    keep_current_username_label,
                    self.conflicting_username_toggle,
                    replace_with_imported_username_label
                ),
                box_to_add_to=conflicting_usernames_box
            )

            add_to_screen(
                widgets_to_add=(
                    imported_data_label,
                    self.imported_data_input,
                    conflicting_usernames_box,
                    save_passwords_button
                ),
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        elif save_passwords:
            passwords_to_save: list[str] = self.imported_data_input.value.split("\n")
            del passwords_to_save[-2:]

            reformatted_passwords_to_save: dict = {}

            print(f"Passwords to save is: {passwords_to_save}")

            service: str = ""
            username: str = ""
            password: str = ""

            for line in passwords_to_save:
                if line == "":
                    service = ""
                    username = ""
                    password = ""
                    continue
                elif line[-1] == " ":
                    line = line[:-1]

                if line[:9] == "Service: ":
                    service = line.replace("Service: ", "").replace("\n", "")
                elif line[:10] == "Username: ":
                    username = line.replace("Username: ", "").replace("\n", "")
                elif line[:10] == "Password: ":
                    password = line.replace("Password: ", "").replace("\n", "")

                if service == "" or username == "" or password == "":
                    continue

                encryption_key = Fernet.generate_key()
                encrypted_key, encryption_iv =  encrypt_data(encryption_key.decode()).values()

                if service in reformatted_passwords_to_save.keys():
                    reformatted_passwords_to_save[service][username] = {
                        "password": Fernet(encryption_key).encrypt(password.encode()).decode(),
                        "key": encrypted_key.decode()
                    }

                else:
                    reformatted_passwords_to_save[service] = {
                        username: {
                            "password": Fernet(encryption_key).encrypt(password.encode()).decode(),
                            "key": encrypted_key.decode()
                        }
                    }

                if encryption_iv is not None:
                    reformatted_passwords_to_save[service][username]["iv"] = encryption_iv

            print(reformatted_passwords_to_save)

            saved_passwords: dict or str = load_user_data(password_file_path=self.data_file_path)

            if isinstance(saved_passwords, str):
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message="Unable to load saved passwords. " + saved_passwords
                )

                await self.dialog(dialog)
                return None

            for imported_service in reformatted_passwords_to_save.keys():
                for imported_username in reformatted_passwords_to_save[imported_service].keys():
                    if (imported_service in saved_passwords["data"].keys()) and (imported_username in saved_passwords["data"][imported_service].keys()):
                        if self.conflicting_username_toggle.value:
                            saved_passwords["data"][imported_service][imported_username] = reformatted_passwords_to_save[imported_service][imported_username]

                        else:
                            continue
                    elif imported_service in saved_passwords["data"].keys():
                        saved_passwords["data"][imported_service][imported_username] = reformatted_passwords_to_save[imported_service][imported_username]

                    elif imported_service not in saved_passwords["data"].keys():
                        saved_passwords["data"][imported_service] = reformatted_passwords_to_save[imported_service]

                    else:
                        dialog = toga.InfoDialog(
                            title=self.warning_title,
                            message="Unknown situation has occurred while saving imported passwords"
                        )

                        await self.dialog(dialog)

            with open(self.data_file_path, mode="w") as passwords_file:
                json.dump(saved_passwords, passwords_file, indent=4)

            dialog = toga.InfoDialog(
                title=self.success_title,
                message="Successfully imported data from selected file"
            )

            await self.dialog(dialog)

            return self.return_to_home_screen()

        else:
            pattern_label = toga.Label(
                text="Please enter the pattern of your password file below: \nTo define the service, type 'service'. To define the username, type in 'username'. To define the password, type 'password'. If you want to ignore a line, type 'ignore'. \nNOTE: Must have a individual service/username/password section for each service",
                style=self.label_style
            )

            self.data_pattern_input = toga.MultilineTextInput(
                placeholder="service\nusername\npassword",
                style=self.input_style
            )

            file_select_button = toga.Button(
                text="Select password file",
                on_press=partial(
                    self.import_from_file,
                    show_path_dialog=True
                )
            )

            add_to_screen(
                widgets_to_add=(
                    pattern_label,
                    self.data_pattern_input,
                    file_select_button
                ),
                box_to_add_to=self.a_box,
                clear_screen=True
            )

    async def send_data(self, _, ready_to_send: bool = False):
        if ready_to_send is False:
            address_label = toga.Label(
                text="Enter the IP address of the receiving device below: ",
                style=self.label_style
            )
            self.address_input = toga.TextInput(style=self.input_style)

            submit_address_button = toga.Button(
                style=self.button_style,
                text="Submit address",
                on_press = partial(self.send_data, ready_to_send=True)
            )

            add_to_screen(
                widgets_to_add=(
                    address_label,
                    self.address_input,
                    submit_address_button
                ),
                box_to_add_to=self.a_box,
                clear_screen=True
            )

        else:
            try:
                # self.server_queue.put(f"COMMAND SEND ADDRESS {self.addresses_selection.value} PORT {os.environ['PORT']} PATH {self.data_file_path} DONE")

                print(f"Server port is of type: {type(os.environ["PORT"])}")
                print(f"Data path is of type: {type(self.data_file_path.as_posix())}")

                self.server_queue.put(
                    json.dumps(
                        {
                            "command": "send",
                            "address": self.address_input.value,
                            "port": os.environ["PORT"],
                            "path": self.data_file_path.as_posix()
                        }
                    ) + " DONE"
                )

            except Full:
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message="Unable to send command to server. Server queue is full"
                )

                await self.dialog(dialog)
                return self.return_to_home_screen()

            else:
                print(f"COMMAND SEND ADDRESS {self.address_input.value} PORT {os.environ['PORT']} PATH {self.data_file_path} DONE")

    # --------------------- Background functions --------------------- #
    async def server_message_listener(self):
        message_complete: bool = False
        message_from_server: str = ""

        while True:
            if self.logged_in_user:

                try:
                    message_from_server += self.app_queue.get_nowait()

                    if isinstance(message_from_server, bytes):
                        message_from_server = message_from_server.decode()

                    elif not isinstance(message_from_server, str):
                        dialog = toga.ErrorDialog(
                            title=self.error_title,
                            message="Unable to start server message listener. Received unexpected data type"
                        )

                        await self.dialog(dialog)
                        self.main_window.close()
                        break

                except Empty:
                    await asyncio.sleep(0.01)
                    continue

                else:
                    print(f"Message from server: {message_from_server}")

                    if isinstance(message_from_server, bytes):
                        message_from_server = message_from_server.decode()

                    elif not isinstance(message_from_server, str):
                        message_from_server = str(message_from_server)

                    if message_from_server.endswith("DONE"):
                        message_from_server: dict = json_repair.loads(message_from_server)

                        if message_from_server["message_type"] == "error":
                            print("Received error message from server")

                            dialog = toga.ErrorDialog(
                                title=self.error_title,
                                message=message_from_server["message"]
                            )

                            await self.dialog(dialog)
                            return self.return_to_home_screen()

                        elif message_from_server["message_type"] == "error_with_traceback":
                            dialog = toga.StackTraceDialog(
                                title=self.error_title,
                                message=message_from_server["message"],
                                content=message_from_server["traceback"]
                            )

                            await self.dialog(dialog)

                        message_complete = True
                        message_from_server: str = ""

                    elif not message_from_server.endswith("DONE") and message_complete is True:
                        message_complete = False

                    else:
                        continue

            else:
                await asyncio.sleep(0.01)
                continue

    # --------------------- Handler functions --------------------- #
    def on_close_handler(self, *args, **kwargs) -> bool:
        print("on_close_handler called")

        window_can_close: bool

        if self.logged_in_user:
            self.server_queue.put("SHUTDOWN")
            self.app_queue.shutdown()

            try:
                if self.server_queue.empty():
                    window_can_close = True

                else:
                    self.server_queue.shutdown(immediate=True)
                    window_can_close = True

            except AttributeError:
                window_can_close = True

        else:
            window_can_close = True

        print(f"Can window close? {window_can_close}")
        return window_can_close

def main():
    return BastionPass()
