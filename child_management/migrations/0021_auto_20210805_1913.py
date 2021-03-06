# Generated by Django 3.1.2 on 2021-08-05 19:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('child_management', '0020_auto_20210805_1911'),
    ]

    operations = [
        migrations.RunSQL('drop view if exists rep_child_baseline_report'),
        migrations.RunSQL("""create or replace view rep_child_baseline_report as 
                                SELECT mds.id AS state_id,
                                    mds.name AS state_name,
                                    mdd.id AS district_id,
                                    mdd.name AS district_name,
                                    sh.id AS shelter_home_id,
                                    sh.name AS shelter_home_name,
                                    ch.case_number,
                                    COALESCE(ch.first_name, ''::character varying) AS first_name,
                                    COALESCE(ch.middle_name, ''::character varying) AS middle_name,
                                    COALESCE(ch.last_name, ''::character varying) AS last_name,
                                        CASE
                                            WHEN ch.dob IS NULL THEN ''::text
                                            ELSE to_char(ch.dob::timestamp with time zone, 'DD-MM-YYYY'::text)
                                        END AS dob,
                                        CASE
                                            WHEN ch.sex = 1 THEN 'Male'::text
                                            WHEN ch.sex = 2 THEN 'Female'::text
                                            WHEN ch.sex = 3 THEN 'Intersex'::text
                                            WHEN ch.sex = 4 THEN 'Transgender'::text
                                            WHEN ch.sex = 5 THEN 'Other'::text
                                            ELSE ''::text
                                        END AS gender,
                                    cc.classification,
                                        CASE
                                            WHEN cfh.flagged_status = 1 THEN 'Yes'::text
                                            ELSE 'No'::text
                                        END AS reco_adoption_inquiry,
                                    csh.admission_number,
                                        CASE
                                            WHEN csh.date_of_admission IS NULL THEN ''::text
                                            ELSE to_char(csh.date_of_admission::timestamp with time zone, 'DD-MM-YYYY'::text)
                                        END AS date_of_admission,
                                    cg.name AS guardian_name,
                                    mdr.name AS guardian_relation,
                                        CASE
                                            WHEN fv.most_recent_visit_date IS NULL THEN 'No Visits'::text
                                            ELSE to_char(fv.most_recent_visit_date::timestamp with time zone, 'DD-MM-YYYY'::text)
                                        END AS guardian_most_recent_visit,
                                        CASE
                                            WHEN cch.last_review_date IS NULL THEN ''::text
                                            ELSE to_char(cch.last_review_date::timestamp with time zone, 'DD-MM-YYYY'::text)
                                        END AS last_review_date,
                                        CASE
                                            WHEN ch.cwc_started_the_process_of_declaring IS NULL THEN ''::text
                                            ELSE to_char(ch.cwc_started_the_process_of_declaring::timestamp with time zone, 'DD-MM-YYYY'::text)
                                        END AS cwc_started_adoption_inquiry,
                                    ch.cwc_order_number,
                                        CASE
                                            WHEN ch.date_declaring_child_free_for_adoption IS NULL THEN ''::text
                                            ELSE to_char(ch.date_declaring_child_free_for_adoption::timestamp with time zone, 'DD-MM-YYYY'::text)
                                        END AS date_declaring_child_free_for_adoption,
                                    ch.remarks
                                FROM child_management_child ch
                                    JOIN ( SELECT row_number() OVER (PARTITION BY child_management_childshelterhomerelation.child_id ORDER BY child_management_childshelterhomerelation.date_of_admission DESC, child_management_childshelterhomerelation.id DESC) AS shelter_num,
                                            child_management_childshelterhomerelation.shelter_home_id,
                                            child_management_childshelterhomerelation.child_id,
                                            child_management_childshelterhomerelation.admission_number,
                                            child_management_childshelterhomerelation.date_of_admission
                                        FROM child_management_childshelterhomerelation
                                        WHERE child_management_childshelterhomerelation.active = 2) csh ON csh.child_id = ch.id AND csh.shelter_num = 1
                                    JOIN master_data_shelterhome sh ON sh.id = csh.shelter_home_id
                                    JOIN master_data_district mdd ON mdd.id = sh.district_id
                                    JOIN master_data_state mds ON mds.id = mdd.state_id
                                    LEFT JOIN ( SELECT x1.child_id,
                                            string_agg(x2.name::text, ', '::text) AS classification
                                        FROM child_management_child_child_classification x1
                                            JOIN master_data_childclassification x2 ON x1.childclassification_id = x2.id AND x2.active = 2
                                        GROUP BY x1.child_id) cc ON ch.id = cc.child_id
                                    LEFT JOIN ( SELECT child_management_guardian.child_id,
                                            row_number() OVER (PARTITION BY child_management_guardian.child_id ORDER BY child_management_guardian.id DESC) AS guardian_num,
                                            child_management_guardian.name,
                                            child_management_guardian.relationship_id
                                        FROM child_management_guardian) cg ON cg.child_id = ch.id AND cg.guardian_num = 1
                                    LEFT JOIN master_data_relationship mdr ON mdr.id = cg.relationship_id
                                    LEFT JOIN ( SELECT child_management_childcwchistory.child_id,
                                            max(child_management_childcwchistory.last_date_of_cwc_order_or_review) AS last_review_date
                                        FROM child_management_childcwchistory
                                        GROUP BY child_management_childcwchistory.child_id) cch ON cch.child_id = ch.id
                                    LEFT JOIN ( SELECT child_management_childflaggedhistory.child_id,
                                            row_number() OVER (PARTITION BY child_management_childflaggedhistory.child_id ORDER BY child_management_childflaggedhistory.flagged_date DESC, child_management_childflaggedhistory.id DESC) AS flagging_num,
                                            child_management_childflaggedhistory.flagged_status
                                        FROM child_management_childflaggedhistory
                                        WHERE child_management_childflaggedhistory.active = 2) cfh ON cfh.child_id = ch.id AND cfh.flagging_num = 1
                                    LEFT JOIN ( SELECT child_management_familyvisit.child_id,
                                            max(child_management_familyvisit.date_of_visit) AS most_recent_visit_date
                                        FROM child_management_familyvisit
                                        GROUP BY child_management_familyvisit.child_id) fv ON ch.id = fv.child_id"""),
        migrations.RunSQL('drop view if exists rep_child_details_view'),
        migrations.RunSQL("""create or replace view rep_child_details_view as 
                                SELECT concat(COALESCE(ch.first_name, ''::character varying), ' ', COALESCE(ch.middle_name, ' '::character varying), ' ', COALESCE(ch.last_name, ''::character varying)) AS child_name,
                                    ch.case_number,
                                        CASE
                                            WHEN ch.dob IS NULL THEN ''::text
                                            ELSE to_char(ch.dob::timestamp with time zone, 'DD-MM-YYYY'::text)
                                        END AS dob,
                                    date_part('year'::text, age(now()::timestamp without time zone, ch.dob::timestamp without time zone)) AS age_year,
                                    date_part('month'::text, age(now()::timestamp without time zone, ch.dob::timestamp without time zone)) AS age_plus_months,
                                        CASE
                                            WHEN ch.sex = 1 THEN 'Male'::text
                                            WHEN ch.sex = 2 THEN 'Female'::text
                                            WHEN ch.sex = 3 THEN 'Transgender'::text
                                            WHEN ch.sex = 4 THEN 'Intersex'::text
                                            WHEN ch.sex = 5 THEN 'Other'::text
                                            ELSE ''::text
                                        END AS gender,
                                        CASE
                                            WHEN fh.flagged_date IS NULL THEN 'NA'::text
                                            ELSE to_char(fh.flagged_date::timestamp with time zone, 'DD-MM-YYYY'::text)
                                        END AS date_flagged_for_adpotion_inquiry,
                                        CASE
                                            WHEN fh.flagged_date IS NULL THEN '-1'::integer::double precision
                                            ELSE date_part('year'::text, age(now()::timestamp without time zone, fh.flagged_date::timestamp without time zone))
                                        END AS adoption_inquiry_pending_years,
                                        CASE
                                            WHEN fh.flagged_date IS NULL THEN '-1'::integer::double precision
                                            ELSE date_part('month'::text, age(now()::timestamp without time zone, fh.flagged_date::timestamp without time zone))
                                        END AS adoption_inquiry_pending_months,
                                        CASE
                                            WHEN fv.most_recent_visit_date IS NOT NULL THEN to_char(fv.most_recent_visit_date::timestamp with time zone, 'DD-MM-YYYY'::text)
                                            ELSE 'No Family Visits'::text
                                        END AS last_family_visit,
                                        CASE
                                            WHEN cg.child_id IS NULL THEN 'No'::text
                                            ELSE 'Yes'::text
                                        END AS guardian_listed,
                                    cc.classification,
                                        CASE
                                            WHEN cs.stay_in_months IS NULL THEN 'NA'::text
                                            WHEN cs.stay_in_months = 0::double precision AND cs.additional_days < 30::double precision THEN '< 1 month'::text
                                            ELSE ((
                                            CASE
                                                WHEN (cs.stay_in_months + (cs.additional_days / 30::double precision)::integer::double precision) >= 12::double precision AND (cs.stay_in_months + (cs.additional_days / 30::double precision)::integer::double precision) < 24::double precision THEN floor(((cs.stay_in_months + floor(cs.additional_days / 30::double precision)::numeric::integer::double precision) / 12::double precision)::numeric) || ' year and '::text
                                                WHEN (cs.stay_in_months + (cs.additional_days / 30::double precision)::integer::double precision) >= 24::double precision THEN floor(((cs.stay_in_months + floor((cs.additional_days / 30::double precision)::numeric)::integer::double precision) / 12::double precision)::numeric) || ' years and '::text
                                                ELSE ''::text
                                            END || ((cs.stay_in_months + floor((cs.additional_days / 30::double precision)::numeric)::integer::double precision)::integer % 12)) || ' month'::text) ||
                                            CASE
                                                WHEN ((cs.stay_in_months + floor((cs.additional_days / 30::double precision)::numeric)::integer::double precision)::integer % 12) > 1 THEN 's'::text
                                                ELSE ''::text
                                            END
                                        END AS total_shelter_home_stay,
                                        CASE
                                            WHEN cr.num_months_last_review IS NULL THEN 'NA'::text
                                            WHEN cr.num_months_last_review = 0::double precision THEN '< 1 month'::text
                                            WHEN cr.num_months_last_review > 0::double precision THEN ((
                                            CASE
                                                WHEN cr.num_months_last_review >= 12::double precision AND cr.num_months_last_review < 24::double precision THEN floor((cr.num_months_last_review / 12::double precision)::numeric) || ' year and '::text
                                                WHEN cr.num_months_last_review >= 24::double precision THEN floor((cr.num_months_last_review / 12::double precision)::numeric) || ' years and '::text
                                                ELSE ''::text
                                            END || (cr.num_months_last_review::integer % 12)) || ' month'::text) ||
                                            CASE
                                                WHEN (cr.num_months_last_review::integer % 12) > 1 THEN 's'::text
                                                ELSE ''::text
                                            END
                                            ELSE NULL::text
                                        END AS last_cwc_review_duration,
                                    fh.flagging_reason,
                                        CASE
                                            WHEN csh.date_of_admission IS NULL THEN 'NA'::text
                                            ELSE to_char(csh.date_of_admission::timestamp with time zone, 'DD-MM-YYYY'::text)
                                        END AS date_of_admission,
                                    csh.admission_number,
                                    sh.name AS shelter_home_name,
                                    sh.id AS shelter_home_id,
                                    mdd.name AS district_name,
                                    mdd.id AS district_id,
                                    mds.name AS state_name,
                                    mds.id AS state_id,
                                    ch.remarks
                                FROM child_management_child ch
                                    JOIN ( SELECT row_number() OVER (PARTITION BY child_management_childshelterhomerelation.child_id ORDER BY child_management_childshelterhomerelation.date_of_admission DESC, child_management_childshelterhomerelation.id DESC) AS shelter_num,
                                            child_management_childshelterhomerelation.shelter_home_id,
                                            child_management_childshelterhomerelation.child_id,
                                            child_management_childshelterhomerelation.admission_number,
                                            child_management_childshelterhomerelation.date_of_admission
                                        FROM child_management_childshelterhomerelation
                                        WHERE child_management_childshelterhomerelation.active = 2) csh ON csh.child_id = ch.id AND csh.shelter_num = 1
                                    JOIN master_data_shelterhome sh ON sh.id = csh.shelter_home_id
                                    JOIN master_data_district mdd ON mdd.id = sh.district_id
                                    JOIN master_data_state mds ON mds.id = mdd.state_id
                                    LEFT JOIN ( SELECT child_management_familyvisit.child_id,
                                            max(child_management_familyvisit.date_of_visit) AS most_recent_visit_date
                                        FROM child_management_familyvisit
                                        GROUP BY child_management_familyvisit.child_id) fv ON ch.id = fv.child_id
                                    LEFT JOIN ( SELECT DISTINCT child_management_guardian.child_id
                                        FROM child_management_guardian
                                        WHERE child_management_guardian.active = 2) cg ON ch.id = cg.child_id
                                    LEFT JOIN ( SELECT x1.child_id,
                                            string_agg(x2.name::text, ', '::text) AS classification
                                        FROM child_management_child_child_classification x1
                                            JOIN master_data_childclassification x2 ON x1.childclassification_id = x2.id AND x2.active = 2
                                        GROUP BY x1.child_id) cc ON ch.id = cc.child_id
                                    LEFT JOIN ( SELECT dash_child_cci_stay_view.child_id,
                                            COALESCE(sum(dash_child_cci_stay_view.stay_in_months), 0::double precision) AS stay_in_months,
                                            COALESCE(sum(dash_child_cci_stay_view.additional_days), 0::double precision) AS additional_days
                                        FROM dash_child_cci_stay_view
                                        GROUP BY dash_child_cci_stay_view.child_id) cs ON cs.child_id = ch.id
                                    LEFT JOIN dash_child_days_lastreview_view cr ON cr.child_id = ch.id
                                    LEFT JOIN ( SELECT child_management_childflaggedhistory.child_id,
                                            row_number() OVER (PARTITION BY child_management_childflaggedhistory.child_id ORDER BY child_management_childflaggedhistory.flagged_date DESC, child_management_childflaggedhistory.id DESC) AS flag_num,
                                            child_management_childflaggedhistory.reason_for_flagging AS flagging_reason,
                                            child_management_childflaggedhistory.flagged_date,
                                            child_management_childflaggedhistory.flagged_status
                                        FROM child_management_childflaggedhistory) fh ON fh.child_id = ch.id AND fh.flag_num = 1
                                WHERE fh.flagged_status = 1"""),
    ]
