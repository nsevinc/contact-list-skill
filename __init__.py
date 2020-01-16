from mycroft import MycroftSkill, intent_file_handler


class ContactList(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('list.contact.intent')
    def handle_list_contact(self, message):
        person = ''

        self.speak_dialog('list.contact', data={
            'person': person
        })


def create_skill():
    return ContactList()

