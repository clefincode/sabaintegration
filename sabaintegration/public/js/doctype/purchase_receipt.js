frappe.ui.form.on('Purchase Receipt', {
    refresh(frm) {
    },
   before_save: function(frm) {
       frm.doc.items.forEach(item => {
           if (item.serial_no) {
               let serial_nos = item.serial_no.split('\n').map(serial => serial.trim());

               serial_nos.forEach(serial_no => {
                   frappe.call({
                       method: 'frappe.client.get_list',
                       args: {
                           doctype: 'Serial No',
                           filters: {
                               name: serial_no
                           },
                           limit_page_length: 1
                       },
                       callback: function(response) {
                           if (!response.message.length) {
                               frappe.call({
                                   method: 'erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle.create_serial_nos',
                                   args: {
                                       item_code: item.item_code,
                                       serial_nos: serial_no
                                   },
                                   callback: function(response) {
                                       if (response.message) {
                                           console.log("serial nos created")
                                       }
                                   }
                               });
                           } 
                       }
                   });
               });
           }
       });
   }
});
