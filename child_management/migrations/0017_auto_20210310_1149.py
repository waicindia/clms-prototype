# Generated by Django 3.1.2 on 2021-03-10 11:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('child_management', '0016_auto_20210308_0934'),
    ]

    operations = [
    migrations.RunSQL('drop view if exists dash_recommended_adoption_view'),
    migrations.RunSQL("""create or replace view dash_recommended_adoption_view as 
    select mds.id as state_id, mds.name as state_name, 
    mdd.id as district_id, mdd.name as district_name, 
    sh.id as shelter_home_id, sh.name as shelter_homename, 
    csr.child_id,
    cfh.flagged_status as flagged_status,
    cfh.flagged_date as reco_ready_date,
    to_char(cfh.flagged_date, 'Mon ''YY') as reco_ready_month
    from child_management_child cc
    inner join (
        select row_number() over (partition by child_id order by date_of_admission desc) as shelter_num, shelter_home_id, child_id, admission_number, date_of_admission
        from  child_management_childshelterhomerelation 
        where active = 2
    ) csr on cc.id = csr.child_id and csr.shelter_num = 1 and cc.active = 2
    inner join master_data_shelterhome sh on csr.shelter_home_id = sh.id 
    inner join master_data_district mdd on sh.district_id = mdd.id and sh.active = 2 
    inner join master_data_state mds on mdd.state_id = mds.id
    left outer join (
        select child_id, row_number() over (partition by child_id order by flagged_date desc) as flagging_num, flagged_status, flagged_date
        from  child_management_childflaggedhistory 
        where active = 2
    ) as cfh on cfh.child_id = cc.id and flagging_num = 1"""),
]
