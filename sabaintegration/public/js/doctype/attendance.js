// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.add_fetch('employee', 'company', 'company');
cur_frm.add_fetch('employee', 'employee_name', 'employee_name');

cur_frm.cscript.onload = function(doc, cdt, cdn) {
	if(doc.__islocal) cur_frm.set_value("attendance_date", frappe.datetime.get_today());
}

cur_frm.fields_dict.employee.get_query = function(doc,cdt,cdn) {
	return{
		query: "erpnext.controllers.queries.employee_query"
	}
}

frappe.ui.form.on('Attendance', {
	finish_on: function(frm) {
		var start = moment(frm.doc.start_on, "HH:mm");
		var end = moment(frm.doc.finish_on, "HH:mm");
		var minutes = end.diff(start, 'minutes');
		var hours = Math.trunc(minutes/60);
		var m1 = minutes%60;		
		frm.set_value('total_working_hours_between_start_and_finish', hours + m1/60 )
	},
	start_on: function(frm) {
		var start = moment(frm.doc.start_on, "HH:mm");
		var end = moment(frm.doc.finish_on, "HH:mm");
		var minutes = end.diff(start, 'minutes');
		var hours = Math.trunc(minutes/60);
		var m1 = minutes%60;		
		frm.set_value('total_working_hours_between_start_and_finish', hours + m1/60 )
		
	},
	total_working_hours_between_start_and_finish: function(frm) {	
		frm.set_value('actual_hours', frm.doc.total_working_hours_between_start_and_finish - frm.doc.not_available_for )	
		
	},
	not_available_for: function(frm) {		
		frm.set_value('actual_hours', frm.doc.total_working_hours_between_start_and_finish - frm.doc.not_available_for )	
	
	},	

	onload: function(frm) {
		if (frm.doc.status=='Absent'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='On Leave'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present' && (frm.doc.location=='Stand By' || frm.doc.location=='Vacation')){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.location=='Stand By' || frm.doc.location=='Vacation'){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present'){
			frm.set_value("work_status_points", get_work_status(frm.doc.location))
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else{
			frm.set_value("work_status_points", get_work_status(frm.doc.location))
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}
	},

	status: function(frm) {
		if (frm.doc.status=='Absent'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='On Leave'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present' && (frm.doc.location=='Stand By' || frm.doc.location=='Vacation')){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.location=='Stand By' || frm.doc.location=='Vacation'){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present'){
			frm.set_value("work_status_points", get_work_status(frm.doc.location))
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else{
			frm.set_value("work_status_points", get_work_status(frm.doc.location))
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}
	},


	location: function(frm) {
		if (frm.doc.status=='Absent'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='On Leave'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present' && (frm.doc.location=='Stand By' || frm.doc.location=='Vacation')){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.location=='Stand By' || frm.doc.location=='Vacation'){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present'){
			frm.set_value("work_status_points", get_work_status(frm.doc.location))
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else{
			frm.set_value("work_status_points", get_work_status(frm.doc.location))
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}
		
	},

	actual_working_hours: function(frm) {
		if (frm.doc.status=='Absent'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='On Leave'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present' && (frm.doc.location=='Stand By' || frm.doc.location=='Vacation')){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.location=='Stand By' || frm.doc.location=='Vacation'){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present'){
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else{
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)		
		}

	},

	productivty: function(frm) {
		if (frm.doc.status=='Absent'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='On Leave'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present' && (frm.doc.location=='Stand By' || frm.doc.location=='Vacation')){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.location=='Stand By' || frm.doc.location=='Vacation'){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present'){
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else{
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}

	},


	team_and_customer_relation: function(frm) {
		if (frm.doc.status=='Absent'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='On Leave'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present' && (frm.doc.location=='Stand By' || frm.doc.location=='Vacation')){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.location=='Stand By' || frm.doc.location=='Vacation'){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present'){
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else{
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)	
		}

	},


	extra_bonus: function(frm) {
		if (frm.doc.status=='Absent'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='On Leave'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present' && (frm.doc.location=='Stand By' || frm.doc.location=='Vacation')){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.location=='Stand By' || frm.doc.location=='Vacation'){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present'){
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else{
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}

	},


	saba_special_bonus: function(frm) {
		if (frm.doc.status=='Absent'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='On Leave'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present' && (frm.doc.location=='Stand By' || frm.doc.location=='Vacation')){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.location=='Stand By' || frm.doc.location=='Vacation'){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present'){
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else{
			frm.set_value("day_appraisal_total", get_working_hours(frm.doc.actual_working_hours)+get_productivity(frm.doc.productivty)+get_team(frm.doc.team_and_customer_relation)+get_extra(frm.doc.extra_bonus)+frm.doc.saba_special_bonus)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}

	},

	working_in_a_vacation_: function(frm) {
		if (frm.doc.status=='Absent'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='On Leave'){
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("work_status_points", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present' && (frm.doc.location=='Stand By' || frm.doc.location=='Vacation')){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.location=='Stand By' || frm.doc.location=='Vacation'){
			frm.set_value("work_status_points", 0)
			frm.set_value("day_appraisal_total", 0)
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else if(frm.doc.status=='Present'){
			frm.set_value("day_total_points", frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}else{
			frm.set_value("day_total_points", get_vacation_worked(frm.doc.working_in_a_vacation_)+frm.doc.day_appraisal_total+frm.doc.work_status_points)
		}

	}


});

function get_work_status(score){
		if(score=='Working From Home'){
			return 8;
		}else if(score=='Office'){
			return 10;
		}else if(score=='Task In Cairo'){
			return 10;
		}else if(score=='Task in Great Cairo'){
			return 12;
		}else if(score=='Overnight Task'){
			return 16;
		}else if(score=='Stand By'){
			return 0;
		}else if(score=='Vacation'){
			return 0;
		}else if(score=='Travelling'){
			return 8;
		}
}

function get_working_hours(score){
		if(score=='-4'){
			return -4;
		}else if(score=='-3'){
			return -3;
		}else if(score=='-2'){
			return -2;
		}else if(score=='-1'){
			return -1;
		}else if(score=='Normal "8"'){
			return 0;
		}else if(score=='+1'){
			return 1;
		}else if(score=='+2'){
			return 2;
		}else if(score=='+3'){
			return 3;
		}else if(score=='+4'){
			return 4;
		}
}

function get_productivity(score){
		if(score=='Very Low Productivity (Equivalent to 0-2:59 HARD-WORKING Hours)'){
			return 1;
		}else if(score=='Below Average (Equivalent to 3-5:59 HARD-WORKING Hours)'){
			return 3;
		}else if(score=='Average (Equivalent to 6-8:59 HARD-WORKING Hours)'){
			return 5;
		}else if(score=='Above Average (Equivalent to 9-10:59 HARD-WORKING Hours)'){
			return 7;
		}else if(score=='Very High Productivity (Equivalent to 11-13:59 HARD-WORKING Hours)'){
			return 10;
		}
}

function get_team(score){
		if(score=='Bad (If received any trusted complains from Team or customers)'){
			return 0;
		}else if(score=='Normal'){
			return 5;
		}else if(score=='Good (If received any trusted praise from Team or customers)'){
			return 10;
		}
}

function get_extra(score){
		if(score=='0'){
			return 0;
		}else if(score=='5 (Participating with an a new accepted idea)'){
			return 5;
		}else if(score=='10 (Solving a problem that the company is facing it for the first time)'){
			return 10;
		}else if(score=="15 (Solving a problem out of the employee's job description)"){
			return 15;
		}
}

function get_vacation_worked(score){
		if(score=='0'){
			return 0;
		}else if(score=='1 Hour (4 Points)'){
			return 4;
		}else if(score=='2 Hours (8 Points)'){
			return 8;
		}else if(score=="3 Hours (12 Points)"){
			return 12;
		}else if(score=="4 Hours (16 Points)"){
			return 16;
		}
}


  

