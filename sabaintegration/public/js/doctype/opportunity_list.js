
// frappe.listview_settings['Opportunity'] = {
//     add_fields: ["status", "status"],
//     // hide_name_column: true,
// 	get_indicator: function(doc)
// 	{	
// 		console.log("dfsdskdjjdsfjnfvk");
//         //Internal Preparation .. cyan
// 		if(doc.status == "Open") {
// 			return [__("Open"), "cyan", "status,=,Open"];
// 		}
// 		else if(doc.status == "Waiting for Technical Reply") {
// 			return [__("Waiting for Technical Reply"), "cyan", "status,=,Waiting for Technical Reply"];
// 		}
// 		else if(doc.status == "Waiting for Consultant/Customer Reply OR Updates") {
// 			return [__("Waiting for Consultant/Customer Reply OR Updates"), "cyan", "status,=,Waiting for Consultant/Customer Reply OR Updates"];
// 		}
//         else if(doc.status == "Waiting for Marketing Response") {
// 			return [__("Waiting for Marketing Response"), "cyan", "status,=,Waiting for Marketing Response"];
// 		}
//         else if(doc.status == "Waiting for Merge and/or Printing") {
// 			return [__("Waiting for Merge and/or Printing"), "cyan", "status,=,Waiting for Merge and/or Printing"];
// 		}
//         else if(doc.status == "Ready for Quoting/Technical Submitting") {
// 			return [__("Ready for Quoting/Technical Submitting"), "cyan", "status,=,Ready for Quoting/Technical Submitting"];
// 		}
//         //Sales Following Up .. blue
//         else if(doc.status == "Technical Proposal submitted & waiting For Consultant/Customer approval") {
// 			return [__("Technical Proposal submitted & waiting For Consultant/Customer approval"), "blue", "status,=,Technical Proposal submitted & waiting For Consultant/Customer approval"];
// 		}
//         else if(doc.status == "Waiting for Tender (Commercial submission) Date") {
// 			return [__("Waiting for Tender (Commercial submission) Date"), "blue", "status,=,Waiting for Tender (Commercial submission) Date"];
// 		}
//         else if(doc.status == "Quotation (Commercial Proposal )has been sent, Waiting for feedback") {
// 			return [__("Quotation (Commercial Proposal )has been sent, Waiting for feedback"), "blue", "status,=,Quotation (Commercial Proposal )has been sent, Waiting for feedback"];
// 		}
//         //Pipeline .. orange
//         else if(doc.status == "Super Hot Deal (Closing in less than a month)") {
// 			return [__("Super Hot Deal (Closing in less than a month)"), "orange", "status,=,Super Hot Deal (Closing in less than a month)"];
// 		}
//         else if(doc.status == "Serious Deal (Closing in the coming 3 months)") {
// 			return [__("Serious Deal (Closing in the coming 3 months)"), "orange", "status,=,Serious Deal (Closing in the coming 3 months)"];
// 		}
//         else if(doc.status == "True opportunity (Closing 3-6 months)") {
// 			return [__("True opportunity (Closing 3-6 months)"), "orange", "status,=,True opportunity (Closing 3-6 months)"];
// 		}
//         //Future Pipeline .. gray
//         else if(doc.status == "Closing 6-9 Months") {
// 			return [__("Closing 6-9 Months"), "gray", "status,=,Closing 6-9 Months"];
// 		}
//         else if(doc.status == "Closing 9-12 Months") {
// 			return [__("Closing 9-12 Months"), "gray", "status,=,Closing 9-12 Months"];
// 		}
//         else if(doc.status == "Closing in more than 1 Year") {
// 			return [__("Closing in more than 1 Year"), "gray", "status,=,Closing in more than 1 Year"];
// 		}
//         //Won .. green
//         else if(doc.status == "Due to best Pricing") {
// 			return [__("Due to best Pricing"), "green", "status,=,Due to best Pricing"];
// 		}
//         else if(doc.status == "Due to providing best technical option") {
// 			return [__("Due to providing best technical option"), "green", "status,=,Due to providing best technical option"];
// 		}
//         else if(doc.status == "Due to our technical support") {
// 			return [__("Due to our technical support"), "green", "status,=,Due to our technical support"];
// 		}
//         else if(doc.status == "Customer trust in us") {
// 			return [__("Customer trust in us"), "green", "status,=,Customer trust in us"];
// 		}
//         else if(doc.status == "Stock Availability") {
// 			return [__("Stock Availability"), "green", "status,=,Stock Availability"];
// 		}
//         else if(doc.status == "Multi winning reasons") {
// 			return [__("Multi winning reasons"), "green", "status,=,Multi winning reasons"];
// 		}
//         //Lost .. red
//         else if(doc.status == "Lost Due to High Prices") {
// 			return [__("Lost Due to High Prices"), "red", "status,=,Lost Due to High Prices"];
// 		}
//         else if(doc.status == "Lost Due to Delay of Reply") {
// 			return [__("Lost Due to Delay of Reply"), "red", "status,=,Lost Due to Delay of Reply"];
// 		}
//         else if(doc.status == "Lost Due to Customer Dissatisfaction") {
// 			return [__("Lost Due to Customer Dissatisfaction"), "red", "status,=,Lost Due to Customer Dissatisfaction"];
// 		}
//         else if(doc.status == "Lost Due to Long Delivery Time") {
// 			return [__("Lost Due to Long Delivery Time"), "red", "status,=,Lost Due to Long Delivery Time"];
// 		}
//         else if(doc.status == "Lost because Customer Preferred Another Partner") {
// 			return [__("Lost because Customer Preferred Another Partner"), "red", "status,=,Lost because Customer Preferred Another Partner"];
// 		}
//         //Hold ... diffrent in code and doctype .. yello
//         else if(doc.status == "Project Postponed") {
// 			return [__("Project Postponed"), "yello", "status,=,Project Postponed"];
// 		}
//         else if(doc.status == "Customer Unreachable for more than 3 months") {
// 			return [__("Customer Unreachable for more than 3 months"), "yello", "status,=,Customer Unreachable for more than 3 months"];
// 		}
//         else if(doc.status == "No Response from customer side") {
// 			return [__("No Response from customer side"), "yello", "status,=,No Response from customer side"];
// 		}
//         //Closed .. purple
//         else if(doc.status == "Customer Was just budgeting") {
// 			return [__("Customer Was just budgeting"), "purple", "status,=,Customer Was just budgeting"];
// 		}
//         else if(doc.status == "More than Customer's Budget") {
// 			return [__("More than Customer's Budget"), "purple", "status,=,More than Customer's Budget"];
// 		}
        
//         else if(doc.status == "Project Cancelled") {
// 			return [__("Project Cancelled"), "purple", "status,=,Project Cancelled"];
// 		}
//         else if(doc.status == "Not Interested") {
// 			return [__("Not Interested"), "purple", "status,=,Not Interested"];
// 		}
//         else if(doc.status == "Not In Portfolio") {
// 			return [__("Not In Portfolio"), "purple", "status,=,Not In Portfolio"];
// 		}
//         else if(doc.status == "Too old/No enough data/Test") {
// 			return [__("Too old/No enough data/Test"), "purple", "status,=,Too old/No enough data/Test"];
// 		}
		
// 	},
// };