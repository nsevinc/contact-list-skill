# =============================================================================
# YAPILACAKLAR
# 4- yeni bir tablo oluşturuldusn->
#     b- en son sorulan soru olabilir ?
#     c- konuşan kişi kendini tanıttıktan sonra benim kelimesiyle listede ki bilgiler işlensin
# 5- kişi ekledikten sonra eklenen kişi hafızaya alınsın(active_contents) ve x bilgisini ekle dediğinde otomatik kime ekleneceği belli olsun
# 6- belki kişi eklendikten sonra bazı temel soruları otomatik sorup verileri doldurabiliriz ?
# =============================================================================
from mycroft import MycroftSkill, intent_handler
from mycroft.util import LOG
import sqlite3
from sqlite3 import Error
import datetime

# =============================================================================
# DB Connection Class
# =============================================================================
class ContactListDB:
    def __init__(self, path=""):
        try:
            self.connectdb = sqlite3.connect(path + '/ContactList.db')
            self.concur = self.connectdb.cursor()
            self.errormessage = ''
            # LOG.info("DB connection connected")   
        except Error as error:
            LOG.warning("Error while connecting to sqlite : {}".format(error))
            
    def createbasedb(self):
        try:
            tablequery = "CREATE TABLE IF NOT EXISTS persons (id integer PRIMARY KEY,first_name TEXT,relation TEXT,mobile_phone TEXT)"
            tablequery2 = "CREATE TABLE IF NOT EXISTS active_contexts (type	TEXT UNIQUE,value TEXT UNIQUE,date	TEXT);"
            self.concur.execute(tablequery)        
            self.concur.execute(tablequery2)        
            self.connectdb.commit()
        except Error as error:
            LOG.error("Bu ne hatası acaba  = " + error)
     
    def returnQuery(self, query, return_type="Single"):
        if return_type == "Single":
            return self.concur.execute(query).fetchone()[0] # Returns a single object
        if return_type == "row":
            return self.concur.execute(query).fetchone() # Returns a row
        if return_type == "all":
            return self.concur.execute(query).fetchall() # Returns a n x n table
        
    def execsql(self, query):
        self.concur.execute(query)
        # LOG.info("SQL executed : {}".format(query))
        
    def selectsql(self, query):
        # LOG.info("SQL executed : {}".format(query))
        return self.concur.execute(query).fetchall()
    
    def createperson(self, person):
        try:
            insertquery = f"INSERT INTO persons (first_name) VALUES ('{person}')"
            self.concur.execute(insertquery)
            self.connectdb.commit()
            return True
        except Error as err:
            self.errormessage = err
            LOG.error("Error : {}".format(err))
            return False
    
    def commit(self):
        try:
            self.connectdb.commit()
            # LOG.info("DB committed")
        except Error as err:
            LOG.error("Error : ".format(err))
        
    def close(self):
        self.connectdb.close()
        # LOG.info("DB connection closed") 

# =============================================================================
# MyCroft Skill Class        
# =============================================================================
class ContactList(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        sqliteConnection = ContactListDB(self.file_system.path)  
        sqliteConnection.createbasedb()
        sqliteConnection.close()
        
# =============================================================================
#     Adding new person if not exist
# =============================================================================
    @intent_handler('new.contact.intent')
    def handle_add_new_contact(self, message):
        sqliteConnection = ContactListDB(self.file_system.path)  
        
        person = message.data.get('person')
        if person is None:
            kisi = self.get_response('who.will.be.added')
            if kisi:
                if self.is_person_exist(kisi) == 0:
                    if sqliteConnection.createperson(kisi):
                        self.speak_dialog('new.contact.added', data={'person':kisi})
                    else:
                        self.speak_dialog('error.message', data={'message':sqliteConnection.errormessage})
                else:
                    self.speak_dialog('this.person.is.available', data={'person':kisi})
            return True
        else:
            if self.is_person_exist(person) == 0:
                if sqliteConnection.createperson(person):
                    self.speak_dialog('new.contact.added', data={'person':person})
                else:
                    self.speak_dialog('error.message', data={'message':sqliteConnection.errormessage})    
            else:
                self.speak_dialog('this.person.is.available', data={'person':person})
                
        sqliteConnection.close()

# =============================================================================
#   Get mobile number functions
# =============================================================================
    @intent_handler('get.mobile.number.intent')   
    def handle_get_mobile_phone(self,message):
        
        person = message.data.get('person')
        if person is not None:
            if self.is_person_exist(person) == 1:
                sqliteConnection = ContactListDB(self.file_system.path)  
                veri = sqliteConnection.returnQuery("select mobile_phone from persons where first_name = '"+person+"'","Single")
                if veri is None or veri == '':
                    question = self.get_response('ask.phone.number', data={'person':person})
                    if question in self.translate_list('yes'):
                        mphonenum = self.get_response('ask.for.phone.number', data={'person':person})
                        if self.update_phone_number(sqliteConnection,person,mphonenum):
                            self.speak_dialog('phone.numbers.saved', data={'person':person,'mphone':mphonenum})
                    else:
                        self.speak_dialog("dont.want.to.add.phone")
                else:
                    self.speak_dialog('phone.number.is.this', data={'person':person,'mphone':veri})
            else:
                self.speak_dialog('dont.know.who.is', data={'person':person})
            sqliteConnection.close()
        else: #if active person is avaible
            active_person = self.get_active_person()
            if active_person != '':
                if self.is_person_exist(active_person) == 1:
                    sqliteConnection = ContactListDB(self.file_system.path)  
                    veri = sqliteConnection.returnQuery("select mobile_phone from persons where first_name = '"+active_person+"'","Single")
                    if veri is None or veri == '':
                        question = self.get_response('ask.phone.number', data={'person':active_person})
                        if question in self.translate_list('yes'):
                            mphonenum = self.get_response('ask.for.phone.number', data={'person':active_person})
                            if self.update_phone_number(sqliteConnection,active_person,mphonenum):
                                self.speak_dialog('phone.numbers.saved', data={'person':active_person,'mphone':mphonenum})
                        else:
                            self.speak_dialog("dont.want.to.add.phone")
                    else:
                        self.speak_dialog('phone.number.is.this', data={'person':active_person,'mphone':veri})
                else:
                    self.speak_dialog('dont.know.who.is', data={'person':active_person})
                sqliteConnection.close()
            else:
                self.speak_dialog('whose.phone.number')
            
        
    def update_phone_number(self,dbconn ,person,mpnumber):
        try:
            dbconn.execsql(f"UPDATE persons SET mobile_phone='{mpnumber}' WHERE first_name='{person}'")
            dbconn.commit()
            return True
        except Error as err:
            self.speak_dialog('error.message', data={'message':err}) 
            return False
    
# =============================================================================
#     Checking person name if it is exist return 1        
# =============================================================================
    def is_person_exist(self,p=""):
        sqliteConnection = ContactListDB(self.file_system.path)  
        result = sqliteConnection.returnQuery("select count(first_name) from persons where first_name = '"+p+"'","Single")
        
        if self.set_active_person(p):
            self.log.info(f"{p} aktif kişi olarak ayarlandı")
        if result < 1:
            # self.log.info("%s kişisi bulunamadı",p)
            sqliteConnection.close()
            return 0
        else:
            # self.log.info("%s kişi bulundu",p)
            sqliteConnection.close()
            return 1
        
    def set_active_person(self,p=""):
        sqliteConnection = ContactListDB(self.file_system.path)  
        isempty = sqliteConnection.returnQuery(f"select count(value) from active_contexts where type = 'person'","Single")
        dtime = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        try:
            if isempty < 1:
                sqliteConnection.execsql(f"INSERT INTO active_contexts (type,value,date) VALUES ('person','{p}','{dtime}')")
            else:
                sqliteConnection.execsql(f"UPDATE active_contexts SET date='{dtime}', value='{p}' WHERE type = 'person'")
            
            sqliteConnection.commit()
            sqliteConnection.close()
            return True
        except Error as err:
            self.speak_dialog('error.message', data={'message':err}) 
            sqliteConnection.close()
            return False
        
    
    def get_active_person(self):
        sqliteConnection = ContactListDB(self.file_system.path)  
        
        result = sqliteConnection.returnQuery(f"select value from active_contexts where type = 'person'","row")
        sqliteConnection.close()
        if result is not None:
            return result[0]
        else:
            return ''
        
        
        
    def stop(self):
        pass

def create_skill():
    return ContactList()

