import sqlite3 as sq


class DataBase:
    """Класс для управления базой данных заметок
        Создание класса для управления базы данных заметок
        file - название базы данных в .bd формате"""
    
    def __init__(self, file: str) -> None:
        """Создание класса для управления базы данных заметок
        file - название базы данных в .db формате"""
        self.file = file        
        with sq.connect(file) as connection:
            cursor = connection.cursor()
            # включить внешние ключи
            connection.execute('PRAGMA foreign_keys = ON;')

            # все объекты
            objects = '''
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                parent INTEGER REFERENCES objects(id)
                )'''
            cursor.execute(objects)

            # папки
            folders = '''
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER REFERENCES notes(id),
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                theme TEXT,
                content TEXT NOT NULL
                )'''
            cursor.execute(folders)
            
            # записи
            notes = '''
            CREATE TABLE IF NOT EXISTS notes (
                date TEXT NOT NULL,
                theme TEXT,
                name TEXT NOT NULL,
                id INTEGER REFERENCES objects(id)
                )'''
            cursor.execute(notes)
            
            # контент записей
            notes_data = '''
            CREATE TABLE IF NOT EXISTS notes_data (
                note_id INTEGER REFERENCES notes(id),
                note_data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_data_type TEXT NOT NULL,
                note_data_coords TEXT NOT NULL,
                note_data_content BLOB,
                note_data_size TEXT NOT NULL,
                note_data_args TEXT
                )'''
            cursor.execute(notes_data)
            
            # корневая папка
            main_directory = '''
            CREATE TABLE IF NOT EXISTS main_directory (
            id_obj INTEGER REFERENCES objects(id)
            )'''
            cursor.execute(main_directory)
            
            connection.commit()
            cursor.close()
        connection.close()

    def info_about_all_notes(self) -> list:
        """Получить информацию обо всех заметка в формате дата, тема, имя, ИД"""
        with sq.connect(self.file) as connection:
            data = list(connection.execute("""SELECT date, theme, name, id FROM notes"""))
        connection.close()        
        return data

    def add_note(self, date: str, name: str, theme: str, directory_id: int) -> None:
        '''Добавить заметку
        корневая директория - 0'''
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            cursor.execute('INSERT INTO objects (type, parent) VALUES (?, ?)', ('notes', directory_id))
            id_note = cursor.lastrowid
            cursor.execute('INSERT INTO notes (date, name, theme, id) VALUES (?, ?, ?, ?)', (date, name, theme, id_note))
            if directory_id:
                cursor.execute('UPDATE folders SET content = content || " " || (?) WHERE id = (?)',
                               (id_note, directory_id))
            else:
                cursor.execute('INSERT INTO main_directory (id_obj) VALUES (?)', (id_note,))
                
            connection.commit()
            cursor.close()
        connection.close()
        
    def add_folder(self, date: str, name: str, theme: str, directory_id: int) -> None:
        '''Добавить папку
        корневая диреуктория - 0'''
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            cursor.execute('INSERT INTO objects (type, parent) VALUES (?, ?)', ('folders', directory_id))
            folder_id = cursor.lastrowid
            cursor.execute('INSERT INTO folders (id, date, name, theme, content) VALUES (?, ?, ?, ?, ?)',
                           (folder_id, date, name, theme, ''))
            if directory_id:
                cursor.execute('UPDATE folders SET content = content || " " || (?) WHERE id = (?)',
                               (folder_id, directory_id))
            else:
                cursor.execute('INSERT INTO main_directory (id_obj) VALUES (?)', (folder_id,))
            cursor.close()
        connection.close()

    def delete_file(self, id: int):
        '''Удалить файл'''
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            if self.get_type_file(id) == 'folders':
                data = cursor.execute('SELECT content FROM folders WHERE id = (?)', (id, )).fetchone()[0]
                for i in data.split():
                    self.delete_file(int(i))
                parent = int(cursor.execute('SELECT parent FROM objects WHERE id = (?)', (id, )).fetchone()[0])
                cursor.execute('DELETE FROM objects WHERE id = (?)', (id, ))
                cursor.execute('DELETE FROM folders WHERE id = (?)', (id, ))
                if parent:
                    content = cursor.execute('SELECT content FROM folders WHERE id = (?)', (parent, )).fetchone()[0]
                    content = content.split()
                    content.remove(str(id))
                    content = ' '.join(content)
                    cursor.execute('UPDATE folders SET content = (?) WHERE id = (?)', (content, parent))
                else:
                    cursor.execute('DELETE FROM main_directory WHERE id_obj = (?)', (id, ))
            else:
                parent = int(cursor.execute('SELECT parent FROM objects WHERE id = (?)', (id, )).fetchone()[0])
                cursor.execute('DELETE FROM objects WHERE id = (?)', (id, ))
                cursor.execute('''DELETE FROM notes_data WHERE note_id=?''', (id, ))
                cursor.execute('DELETE FROM notes WHERE id = (?)', (id, ))
                if parent:
                    content = cursor.execute('SELECT content FROM folders WHERE id = (?)', (parent, )).fetchone()[0]
                    content = content.split()
                    content.remove(str(id))
                    content = ' '.join(content)
                    cursor.execute('UPDATE folders SET content = (?) WHERE id = (?)', (content, parent))
                else:
                    cursor.execute('DELETE FROM main_directory WHERE id_obj = (?)', (id, ))
                cursor.close()
        connection.close()
        
    def check_main_directory(self) -> list:
        """Получить id элементов в корневой директории"""
        with sq.connect(self.file) as connection:
            data = list(connection.execute('SELECT id_obj FROM main_directory'))
        connection.close()
        return data

    def info_about_note(self, id_note: int) -> list:
        """Получить информацию о заметке по id"""
        with sq.connect(self.file) as connection:
            data = list(connection.execute('SELECT * FROM notes WHERE id = (?)', (id_note,)))
        connection.close()
        return data[0]

    def info_about_folder(self, folder_id: int) -> list:
        """Получить информацию о папке по id"""
        with sq.connect(self.file) as connection:
            data = list(connection.execute('SELECT * FROM folders WHERE id = (?)', (folder_id,)))
        connection.close()
        return data[0]

    def get_content_folder(self, direction_id: int) -> list:
        """Получить информацию о папке в формате имя, дата, тема"""
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            if direction_id:
                cursor.execute('SELECT content FROM folders WHERE id = (?)', (direction_id,))
                data = str(cursor.fetchone()[0])
                result = []
                for id_obj in data.split():
                    cursor.execute('SELECT type FROM objects WHERE id = (?)', (id_obj,))
                    type_obj = cursor.fetchone()[0]
                    cursor.execute(f'SELECT name, date, theme FROM {type_obj} WHERE id = (?)', (id_obj,))
                    result.append(cursor.fetchone() + (type_obj, id_obj))
            else:
                cursor.execute('SELECT * FROM main_directory')
                data = cursor.fetchall()
                result = []
                for id_obj in data:
                    cursor.execute('SELECT type FROM objects WHERE id = (?)', (id_obj[0],))
                    type_obj = cursor.fetchone()[0]
                    cursor.execute(f'SELECT name, date, theme FROM {type_obj} WHERE id = (?)', (id_obj[0],))
                    result.append(cursor.fetchone() + (type_obj, id_obj[0]))
                cursor.close()
        connection.close()
        return result

    def get_type_file(self, id_file: int) -> str:
        """Получить тип файла"""
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            data = cursor.execute('SELECT type FROM objects WHERE id = ?', (id_file, )).fetchone()[0]
            cursor.close()
        connection.close()
        return data

    def get_parent_file(self, id_file: int) -> int:
        """Получить нахождение файла"""
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            data = cursor.execute('SELECT parent FROM objects WHERE id = ?', (id_file, )).fetchone()[0]
            cursor.close()
        connection.close()
        return data

    def clear_note_content(self, note_id):
        '''Удалить содержание заметки'''
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            cursor.execute('''DELETE FROM notes_data WHERE note_id=?''', (note_id, ))
            cursor.close()
        connection.close()

    def add_note_content(self, type, coords, size, content, note_id, args=None):
        '''Добавить содержание заметки'''
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            cursor.execute('''
            INSERT INTO notes_data (note_data_type,
            note_data_coords, note_data_size, note_data_content, note_id, note_data_args) VALUES (?, ?, ?, ?, ?, ?)''',
                           (type, coords, size, content, note_id, args))
            cursor.close()
        connection.close()

    def get_note_content(self, note_id):
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            data = cursor.execute('SELECT * FROM notes_data WHERE note_id = ?', (str(note_id), )).fetchall()
            cursor.close()
        connection.close()
        return data

    def change_file_name(self, note_id: int, name: str):
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            cursor.execute(f'UPDATE {self.get_type_file(note_id)} SET name = (?) WHERE id = (?)', (name, note_id))
            cursor.close()
        connection.close()

    def change_file_theme(self, note_id: int, theme: str):
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            cursor.execute(f'UPDATE {self.get_type_file(note_id)} SET theme = (?) WHERE id = (?)', (theme, note_id))
            cursor.close()
        connection.close()

    def remove_file(self, id_file: int, new_directory: int):
        with sq.connect(self.file) as connection:
            cursor = connection.cursor()
            parent_file = self.get_parent_file(id_file)
            if parent_file:
                content = cursor.execute('SELECT content FROM folders WHERE id = (?)', (parent_file, )).fetchone()[0]
                content = content.split()
                content.remove(str(id_file))
                content = ' '.join(content)
                cursor.execute('UPDATE folders SET content = (?) WHERE id = (?)', (content, parent_file))
            else:
                cursor.execute('DELETE FROM main_directory WHERE id_obj = (?)', (id_file, ))
            cursor.execute('UPDATE objects SET parent = (?) WHERE id = (?)', (new_directory, id_file))
            if new_directory:
                cursor.execute('UPDATE folders SET content = content || " " || (?) WHERE id = (?)',
                               (id_file, new_directory))
            else:
                cursor.execute('INSERT INTO main_directory (id_obj) VALUES (?)', (id_file,))
            connection.commit()
            cursor.close()
        connection.close()
