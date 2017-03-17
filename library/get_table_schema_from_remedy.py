from pyars import erars
ars = erars.erARS()
ars.Login('arsystem.isus.emc.com', 'dimsreport', 'report')

for schema in ['EMC:Issue_Audit_join', 'EMC:Issue Notes Join', 'EMC:Issue_Assoc_Instance_join',
               'EMC:SHARE:Employee',
               'EMC:Issue Assigned-to Manager Join', 'EMC:Issue Reported by Manager Join']:
    userFields = ars.GetFieldTable(schema)
    filename = 'table(' + schema.replace(':', ' ') + ').txt'
    with open(filename, "w") as f:
        f.write(str(schema) + '\n')
        f.write('\n')
        for key, value in userFields.iteritems():
            f.write(str(key) + ' : ' + str(value) + '\n')
        f.close()

ars.Logoff()