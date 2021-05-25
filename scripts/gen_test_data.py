from filterapp.models import *
import copy

domains = {1: 3, 2: 6, 3: 10, 4: 13, 5: 16, 6: 20}


def run():
    # gen_domain()
    # gen_domain_entry()
    gen_test_patient()


def gen_domain():
    Domain.objects.all().delete()
    for i in (range(1, len(domains) + 1)):
        Domain.objects.create(id=i, domain_name='DOMAIN' + str(i))


def gen_domain_entry():
    DomainEntry.objects.all().delete()
    for i in (range(1, len(domains) + 1)):
        num_of_entries = domains[i]
        for j in (range(1, num_of_entries + 1)):
            DomainEntry.objects.create(entry_name=str(i) + '.' + str(j), domain_id=i)


def gen_test_patient():
    TestPatientAttribute.objects.all().delete()
    # loop through domains
    patients = []
    for i in (range(1, 7)):
        # num_of_entries = domains[i]
        # entries = DomainEntry.objects.filter(domain_id=i)
        entries = [*range(0, domains[i]+1)]
        print('domain ' + str(i) + ' entries: ' + str(entries))
        patients = add_attr_to_patient(patients, entries)
    print('No. of patients: ' + str(len(patients)))
    # print(patients)
#     save to test patient
    for n, pt in enumerate(patients, start=1):
        # n is patient id
        # print('patient id=' + str(n))
        for m, a in enumerate(pt, start=1):
            # m is domain name
            db_pt = TestPatientAttribute.objects.create(patient_id='PATIENT' + str(n), domain_name='DOMAIN' + str(m), attribute_name='ATTRIBUTE' + str(a))
    # count total patients
    print(TestPatientAttribute.objects.values('patient_id').distinct().count())


def add_attr_to_patient(patients, domain_entries):
    new_ptlist = []
    for en in domain_entries:
        if len(patients) == 0:
            new_pt = [en]
            new_ptlist.append(new_pt)
        for pt in patients:
            new_pt = copy.deepcopy(pt)
            new_pt.append(en)
            new_ptlist.append(new_pt)
    return new_ptlist


