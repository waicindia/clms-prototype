# Generated by Django 3.1.2 on 2021-03-12 05:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('child_management', '0017_auto_20210310_1149'),
    ]

    operations = [
    migrations.RunSQL('drop view if exists dash_recommended_adoption_view'),
    migrations.RunSQL('drop view if exists rep_child_details_view'),
    migrations.RunSQL('drop view if exists rep_child_baseline_report'),
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
    migrations.RunSQL("""create or replace view rep_child_details_view as 
                            select 
                            concat(coalesce(ch.first_name,''), ' ', coalesce(ch.middle_name,' '), ' ', coalesce(ch.last_name,'')) as child_name,
                            ch.case_number,
                            (case when ch.dob is null then '' else to_char(ch.dob, 'DD-MM-YYYY') end) as dob,
                            extract( year  from (age(now()::TIMESTAMP, ch.dob::TIMESTAMP))) as age_year,
                            extract( month  from (age(now()::TIMESTAMP, ch.dob::TIMESTAMP))) as age_plus_months,
                            (case when ch.sex = 1 then 'Male' when ch.sex = 2 then 'Female' when ch.sex = 3 then 'Transgender' when ch.sex = 4 then 'Intersex' when ch.sex = 5 then 'Other' else '' end) as gender,
                            (case when fh.flagged_date is null then 'NA' else to_char(fh.flagged_date, 'DD-MM-YYYY') end) as date_flagged_for_adpotion_inquiry,
                            (case when fh.flagged_date is null then -1 else extract( year  from (age(now()::TIMESTAMP, fh.flagged_date::TIMESTAMP))) end) as adoption_inquiry_pending_years,
                            (case when fh.flagged_date is null then -1 else extract( month  from (age(now()::TIMESTAMP, fh.flagged_date::TIMESTAMP))) end) as adoption_inquiry_pending_months,
                            case when fv.most_recent_visit_date is not null then to_char(fv.most_recent_visit_date, 'DD-MM-YYYY') else 'No Family Visits' end as last_family_visit,
                            (case when cg.child_id is null then 'No' else 'Yes' end) as guardian_listed,
                            cc.classification, 
                            (case when cs.stay_in_months is null then 'NA' when cs.stay_in_months = 0 then '< 1 month' else ((case when cs.stay_in_months >= 12 and cs.stay_in_months <24 then floor((cs.stay_in_months/12)::numeric) || ' year and '
                                when cs.stay_in_months >= 24 then floor((cs.stay_in_months/12)::numeric) || ' years and ' else ''
                            end) || (cs.stay_in_months::int % 12) || ' month' || (case when (cs.stay_in_months::int % 12) > 1 then 's' else '' end)) end) as total_shelter_home_stay,
                            (case when cr.num_months_last_review is null then 'NA' when cr.num_months_last_review = 0 then '< 1 month' when cr.num_months_last_review > 0 then ((case when cr.num_months_last_review >= 12 and cr.num_months_last_review <24 then floor((cr.num_months_last_review/12)::numeric) || ' year and '
                                when cr.num_months_last_review >= 24 then floor((cr.num_months_last_review/12)::numeric) || ' years and ' else ''
                            end) || (cr.num_months_last_review::int % 12) || ' month' || (case when (cr.num_months_last_review::int % 12) > 1 then 's' else '' end)) end) as last_cwc_review_duration,
                            fh.flagging_reason,
                            (case when csh.date_of_admission is null then 'NA' else to_char(csh.date_of_admission, 'DD-MM-YYYY') end) as date_of_admission,
                            csh.admission_number,
                            sh.name as shelter_home_name,
                            sh.id as shelter_home_id,
                            mdd.name as district_name,
                            mdd.id as district_id,
                            mds.name as state_name,
                            mds.id as state_id
                            from child_management_child ch
                            inner join (
                                select row_number() over (partition by child_id order by date_of_admission desc) as shelter_num, shelter_home_id, child_id, admission_number, date_of_admission
                                from  child_management_childshelterhomerelation 
                                where active = 2
                            ) as csh on csh.child_id = ch.id and csh.shelter_num = 1 
                            inner join master_data_shelterhome sh on sh.id = csh.shelter_home_id
                            inner join master_data_district mdd on mdd.id = sh.district_id
                            inner join master_data_state mds on mds.id = mdd.state_id
                            left outer join (
                                select child_id, max(date_of_visit) as most_recent_visit_date
                                from child_management_familyvisit
                                group by child_id
                            ) as fv on ch.id = fv.child_id
                            left outer join (select distinct child_id from child_management_guardian where active = 2) as cg on ch.id = cg.child_id
                            left outer join (
                                select child_id, string_agg(x2.name, ', ') as classification
                                from child_management_child_child_classification x1
                                inner join master_data_childclassification x2 on x1.childclassification_id = x2.id and x2.active = 2
                                group by child_id
                            ) as cc on ch.id = cc.child_id
                            left outer join (select child_id, sum(stay_in_months) as stay_in_months
                                from dash_child_cci_stay_view 
                                group by child_id
                            ) as cs on cs.child_id = ch.id
                            left outer join dash_child_days_lastreview_view cr on cr.child_id = ch.id 
                            left outer join (
                                select child_id, row_number() over(partition by child_id order by flagged_date desc) as flag_num, reason_for_flagging as flagging_reason, flagged_date, flagged_status
                                from child_management_childflaggedhistory 
                            ) as fh on fh.child_id = ch.id and fh.flag_num = 1
                            where fh.flagged_status = 1"""),
    migrations.RunSQL("""create or replace view rep_child_baseline_report as 
                            select 
                            mds.id as state_id,
                            mds.name as state_name,
                            mdd.id as district_id,
                            mdd.name as district_name,
                            sh.id as shelter_home_id,
                            sh.name as shelter_home_name,
                            ch.case_number,
                            coalesce(ch.first_name,'') as first_name, 
                            coalesce(ch.middle_name,'') as middle_name,
                            coalesce(ch.last_name,'') as last_name,
                            (case when ch.dob is null then '' else to_char(ch.dob, 'DD-MM-YYYY') end) as dob,
                            (case when ch.sex = 1 then 'Male' when ch.sex = 2 then 'Female' when ch.sex = 3 then 'Intersex' when ch.sex = 4 then 'Transgender' when ch.sex = 5 then 'Other' else '' end) as gender,
                            cc.classification, 
                            (case when cfh.flagged_status = 1 then 'Yes' else 'No' end) reco_adoption_inquiry,
                            csh.admission_number,
                            (case when csh.date_of_admission is null then '' else to_char(csh.date_of_admission, 'DD-MM-YYYY') end) as date_of_admission,
                            cg.name as guardian_name,
                            mdr.name as guardian_relation,
                            (case when fv.most_recent_visit_date is null then 'No Visits' else to_char(fv.most_recent_visit_date, 'DD-MM-YYYY') end) as guardian_most_recent_visit,
                            (case when cch.last_review_date is null then '' else to_char(cch.last_review_date, 'DD-MM-YYYY') end) as last_review_date,
                            (case when ch.cwc_started_the_process_of_declaring is null then '' else to_char(ch.cwc_started_the_process_of_declaring, 'DD-MM-YYYY') end) as cwc_started_adoption_inquiry,
                            ch.cwc_order_number as cwc_order_number,
                            (case when ch.date_declaring_child_free_for_adoption is null then '' else to_char(ch.date_declaring_child_free_for_adoption, 'DD-MM-YYYY') end) as date_declaring_child_free_for_adoption
                            from child_management_child ch
                            inner join (
                                select row_number() over (partition by child_id order by date_of_admission desc) as shelter_num, shelter_home_id, child_id, admission_number, date_of_admission
                                from  child_management_childshelterhomerelation 
                                where active = 2
                            ) as csh on csh.child_id = ch.id and csh.shelter_num = 1 
                            inner join master_data_shelterhome sh on sh.id = csh.shelter_home_id
                            inner join master_data_district mdd on mdd.id = sh.district_id
                            inner join master_data_state mds on mds.id = mdd.state_id
                            left outer join (
                                select child_id, string_agg(x2.name, ', ') as classification
                                from child_management_child_child_classification x1
                                inner join master_data_childclassification x2 on x1.childclassification_id = x2.id and x2.active = 2
                                group by child_id
                            ) as cc on ch.id = cc.child_id
                            left outer join (
                                select child_id, row_number() over (partition by child_id order by id desc) as guardian_num, name, relationship_id
                                from child_management_guardian 
                            ) cg on cg.child_id = ch.id and cg.guardian_num = 1
                            left outer join master_data_relationship mdr on mdr.id = cg.relationship_id
                            left outer join (
                                    select child_id, max(last_date_of_cwc_order_or_review) as last_review_date
                                    from child_management_childcwchistory 
                                    group by child_id
                            ) as cch on cch.child_id = ch.id
                            left outer join (
                                select child_id, row_number() over (partition by child_id order by flagged_date desc) as flagging_num, flagged_status
                                from  child_management_childflaggedhistory 
                                where active = 2
                            ) as cfh on cfh.child_id = ch.id and flagging_num = 1
                            left outer join (
                                select child_id, max(date_of_visit) as most_recent_visit_date
                                from child_management_familyvisit
                                group by child_id
                            ) as fv on ch.id = fv.child_id"""),
]