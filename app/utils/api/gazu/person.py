from app.core.gazu_client import gazu_client

class PersonServices:
    @staticmethod
    def get_persons():
        return gazu_client.person.all_persons()

    @staticmethod
    def get_person_by_id(person_id):
        return gazu_client.person.get_person(person_id)

    @staticmethod
    def get_person_by_name(full_name):
        return gazu_client.person.get_person_by_full_name(full_name)

    @staticmethod
    def get_person_by_email(email):
        return gazu_client.person.get_person_by_email(email)

    @staticmethod
    def get_departments():
        return gazu_client.person.all_departments()

    @staticmethod
    def get_department_by_id(department_id):
        return gazu_client.person.get_department(department_id)

    @staticmethod
    def get_department_by_name(department_name):
        return gazu_client.person.get_department_by_name(department_name)
    