frappe.ui.form.on("Task", {
    refresh: function(frm){
        if (!frm.is_new() && frm.doc.project)
        {
            frm.add_custom_button("Add client user to follow doc", async function(){
                var users = await frappe.call({
                    method: "sabaintegration.www.api.get_clients",
                    args:{
                        'project': frm.doc.project
                    },
                    callback: function(r){
                        return r.message
                    }
                })
                var d = new frappe.ui.Dialog({
                    title: __('Add Client'),
                    
                    fields: [{
                        "label": "Client User",
                        "fieldname": "user",
                        "fieldtype": "Select",
                        "options": users.message,
                    }],
                    primary_action: function() {
                        var user = d.get_values().user;
                        frappe.call({
                        method: "frappe.desk.form.document_follow.follow_document",
                        args: {
                            'doctype': frm.doc.doctype,
                            'doc_name': frm.doc.name,
                            'user': user
                        },
                        freeze: true,
                        callback: function(r) {
                            d.hide();
                        }
                    });
                        
                    }
                })
                d.show();
            })
        }
        
        $(".btn-comment").click(function() {
            var comment = $('.comment-input-container .ql-editor p')[0].innerHTML;
            if (comment == '' || comment == '<br>'){
                return
            }
            frappe.call({
                method: "sabaintegration.www.api.send_updates",
            })
        })
    }
})
