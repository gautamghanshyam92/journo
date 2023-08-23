/* API's to perform GET, PUT, POST, DELETE on Settings -> Categories */
function getCategoryDetailsForUpdate(id) {
  var categoryId = id.split('-')[1];

  $.ajax({
    type: "GET",
    url: "/categories/" + categoryId.toString(),
    contentType: 'application/json',
    success: function (data, status, xhr) { 
          var categoryIdField = document.getElementById("input_category_id")
          categoryIdField.value = data["_id"]

          var categoryNameField = document.getElementById("input_category_name")
          categoryNameField.value = data["name"]
      },
    error: function (xhrObj, error, reason) { 
          console.log(reason)
      }
  });
}

function createNewCategory() {
    var categoryName = document.getElementById("new_category_name").value
    var categoryDetails = {"name": categoryName}

    $.ajax({
        type: "POST",
        url: "/categories",
        contentType: 'application/json',
        data: JSON.stringify(categoryDetails),
        success: function (data, status, xhr) {
            if (data.ok == true) {
                var row = '<tr id="category-row-'+data._id+'" class="row">\
                  <td class="col-8">'+data.name+'</td>\
                  <td class="col-4">\
                    <button id=category_edit-'+data._id+' class="table-edit" onclick="getCategoryDetailsForUpdate(this.id)" data-toggle="modal" data-target="#category_modal">Edit</button>\
                    <button id=category_delete-'+data._id+' name='+data.name+' onclick="setCategoryDetailsToBeDeleted(this.id, this.name)" class="table-del" data-toggle="modal" data-target="#category_delete_modal">Delete</button>\
                  </td>\
                </tr>';
                $('#categoryInfoLists tbody').append(row);
            }
        },
    	error: function (xhrObj, error, reason) {
            console.log('Error encountered while creating a new category: ', error);
        }
    });
}

function updateCategoryDetails() {
    var categoryId = document.getElementById("input_category_id").value
    var categoryName = document.getElementById("input_category_name").value
    var updateData = {"name": categoryName}

    $.ajax({
        type: "PUT",
        url: "/categories/" + categoryId.toString(),
        contentType: 'application/json',
        data: JSON.stringify(updateData),
        success: function (data, status, xhr) {
            console.log(data)
            var rowId = "category-row-"+categoryId
            if (data.ok == true) {
                var row = document.getElementById(rowId)
                row.cells[0].innerHTML = categoryName
            }
        },
    	error: function (xhrObj, error, reason) { 
        }
    });
}

function setCategoryDetailsToBeDeleted(id, categoryName) {
    var categoryId = id.split('-')[1];
    document.getElementById("delete_input_category_id").value = categoryId;
    document.getElementById("delete_input_category_name").value = categoryName;
}

function deleteCategory() {
    var categoryId = document.getElementById("delete_input_category_id").value;
    console.log('categoryId::: ', categoryId);
    $.ajax({
        type: "DELETE",
        url: "/categories/" + categoryId.toString(),
        contentType: 'application/json',
        success: function (data, status, xhr) {
            var row = document.getElementById('category-row-'+categoryId);
            var table = document.getElementById('categoryInfoLists');
            if(row && row.rowIndex) {
                table.deleteRow(row.rowIndex);
            }
        },
    	error: function (xhrObj, error, reason) { 
            console.log('Error encountered while deleting the category: ', error);
        }
    });
}

/* API's to perform GET, PUT, POST, DELETE on Settings -> Storage */
function createNewStorage() {
  var storageId = document.getElementById('create_storage_id').value;
  var storageName = document.getElementById("create_storage_name").value;

  var storageDetails = {"name": storageName};
  storageDetails.share_id = storageId;

  var protocol = document.getElementById("create_protocol").value;
  storageDetails.protocols = [protocol];
  storageDetails.rules = {};

  var type = $(".storage_type_create_box:checked").val();
  storageDetails.type = type;
  storageDetails.paths = {};
  if(protocol === 'file') {
    var fileTogSwitch = $('#fileCreateTogSwitch');

    storageDetails.state = 'disabled';
    if(fileTogSwitch.is(':checked')) {
      storageDetails.state = 'active';
    }

    
    storageDetails.paths.file = {
      path: document.getElementById("fileCreatePathUrl").value,
      protocol: protocol,
    }

  } else if(protocol === 'smb') {
    var fileTogSwitch = $('#smbCreateTogSwitch');

    storageDetails.state = 'disabled';
    if(fileTogSwitch.is(':checked')) {
      storageDetails.state = 'active';
    }
    storageDetails.paths.smb = {
      ip: document.getElementById("createSmbIpAddress").value,
      username: document.getElementById("createSmbUserName").value,
      password: document.getElementById("createSmbPassword").value,
      path: document.getElementById("createSmbShareName").value,
      protocol: protocol,
    }
  } else if(protocol === 'ftp') {
    var fileTogSwitch = $('#ftpCreateTogSwitch');

    storageDetails.state = 'disabled';
    if(fileTogSwitch.is(':checked')) {
      storageDetails.state = 'active';
    }

    storageDetails.paths.ftp = {
      ip: document.getElementById("createFtpIpAddress").value,
      port: document.getElementById("createFtpPort").value || 21,
      username: document.getElementById("createFtpUserName").value,
      password: document.getElementById("createFtpPassword").value,
      path: document.getElementById("createFtpOffsetPath").value,
      protocol: protocol,
    }
  } else {
    return false;
  }

  $.ajax({
      type: "POST",
      url: "/shares",
      contentType: 'application/json',
      data: JSON.stringify(storageDetails),
      success: function (data, status, xhr) {
          if (data.ok == true) {
              var row = '<tr id="storage-row-'+data._id+'" class="row">\
                <td id="storage-name-'+data._id+'" class="col-3">'+data.name+'</td>\
                <td id="storage-protocol-'+data._id+'" class="col-3">'+data.protocols[0]+'</td>\
                <td id="storage-state-'+data._id+'" class="col-3">'+data.state+'</td>\
                <td class="col-3">\
                  <button id=storage_edit-'+data._id+'  class="table-edit" onclick="getStorageInfoForUpdate(this.id)"  data-toggle="modal" data-target="#storage_edit_modal">Edit</button>\
                  <button id=storage_delete-'+data._id+' name='+data.name+' onclick="setStorageDetailsToBeDeleted(this.id, this.name)" class="table-del" data-toggle="modal" data-target="#storage_delete_modal">Delete</button>\
                </td>\
              </tr>';
              $('#storageInfoLists tbody').append(row);
          }
      },
    error: function (xhrObj, error, reason) {
          console.log('Error encountered while creating a new storage: ', error);
      }
  });
}

function getStorageInfoForUpdate(id) {
  var storageId = id.split('-')[1];

  $.ajax({
    type: "GET",
    url: "/shares?share_id=" + storageId.toString(),
    contentType: 'application/json',
    success: function (data, status, xhr) {
      console.log(data);
      var storageData = data.shares;
      if (storageData && storageData.length > 0) {
        storageData = storageData[0];
        var protocol = storageData.protocols[0];

        var storageIdInput = document.getElementById("edit_storage_id");
        storageIdInput.value = storageData['_id'];

        var storageNameInput = document.getElementById("edit_storage_name");
        storageNameInput.value = storageData.name;
        $('#editStorageModal .box').hide();
        if (protocol === 'file') {
          var filePathInput = document.getElementById("filePathUrl");
          filePathInput.value = storageData.paths[protocol].path;

          var fileTogSwitch = $('#fileTogSwitch');

          if(fileTogSwitch.is(':checked') === false && storageData.state === 'active' || fileTogSwitch.is(':checked') === true && storageData.state !== 'active') {
            fileTogSwitch.click();
          }

          $('#edit_protocol').val(protocol);
          $('#smb_storage_edit_box').hide();
          $('#ftp_storage_edit_box').hide();
          $('#file_storage_edit_box').show();
          

        } else if (protocol === 'smb') {
          var fileTogSwitch = $('#smbTogSwitch');
          if(fileTogSwitch.is(':checked') === false && storageData.state === 'active' || fileTogSwitch.is(':checked') === true && storageData.state !== 'active') {
            fileTogSwitch.click();
          }

          $('#edit_protocol').val(protocol);
          $('#file_storage_edit_box').hide();
          $('#ftp_storage_edit_box').hide();
          $('#smb_storage_edit_box').show();

          var smbIpAddress = document.getElementById("smbIpAddress");
          smbIpAddress.value = storageData.paths[protocol].ip;

          var smbUserName = document.getElementById("smbUserName");
          smbUserName.value = storageData.paths[protocol].username;

          var smbPassword = document.getElementById("smbPassword");
          smbPassword.value = storageData.paths[protocol].password;

          var smbShareName = document.getElementById("smbShareName");
          smbShareName.value = storageData.paths[protocol].path;
        } else if (protocol === 'ftp') {
          var fileTogSwitch = $('#ftpTogSwitch');
          if(fileTogSwitch.is(':checked') === false && storageData.state === 'active' || fileTogSwitch.is(':checked') === true && storageData.state !== 'active') {
            fileTogSwitch.click();
          }

          $('#edit_protocol').val(protocol);
          $('#file_storage_edit_box').hide();
          $('#smb_storage_edit_box').hide();
          $('#ftp_storage_edit_box').show();

          var ftpIpAddress = document.getElementById("ftpIpAddress");
          ftpIpAddress.value = storageData.paths[protocol].ip;
          
          var ftpPort = document.getElementById("editFtpPort");
          ftpPort.value = storageData.paths[protocol].port;

          var ftpUserName = document.getElementById("ftpUserName");
          ftpUserName.value = storageData.paths[protocol].username;

          var ftpPassword = document.getElementById("ftpPassword");
          ftpPassword.value = storageData.paths[protocol].password;

          var ftpOffsetPath = document.getElementById("ftpOffsetPath");
          ftpOffsetPath.value = storageData.paths[protocol].path;
        }
        $(".storage_type_edit_box[value='"+storageData.type+"']").prop("checked", true);
      }
    },
    error: function (xhrObj, error, reason) {
      console.log('Error while getting the share details: ', error);
    }
  });
}

function updateStorageDetails() {
  var storageId = document.getElementById('edit_storage_id').value;
  var storageName = document.getElementById("edit_storage_name").value;

  var updateData = {"name": storageName};
  updateData.share_id = storageId;

  var protocol = document.getElementById("edit_protocol").value;
  updateData.protocols = [protocol];
  updateData.rules = {};

  var type = $(".storage_type_edit_box:checked").val();
  updateData.type = type;
  updateData.paths = {};
  if(protocol === 'file') {
    var fileTogSwitch = $('#fileTogSwitch');

    updateData.state = 'disabled';
    if(fileTogSwitch.is(':checked')) {
      updateData.state = 'active';
    }

    updateData.paths.file = {
      path: document.getElementById("filePathUrl").value,
      protocol: protocol,
    }

  } else if(protocol === 'smb') {
    var fileTogSwitch = $('#smbTogSwitch');

    updateData.state = 'disabled';
    if(fileTogSwitch.is(':checked')) {
      updateData.state = 'active';
    }
    updateData.paths.smb = {
      ip: document.getElementById("smbIpAddress").value,
      username: document.getElementById("smbUserName").value,
      password: document.getElementById("smbPassword").value,
      path: document.getElementById("smbShareName").value,
      protocol: protocol,
    }
  } else if(protocol === 'ftp') {
    var fileTogSwitch = $('#ftpTogSwitch');

    updateData.state = 'disabled';
    if(fileTogSwitch.is(':checked')) {
      updateData.state = 'active';
    }

    updateData.paths.ftp = {
      ip: document.getElementById("ftpIpAddress").value,
      port: document.getElementById("editFtpPort").value || 21,
      username: document.getElementById("ftpUserName").value,
      password: document.getElementById("ftpPassword").value,
      path: document.getElementById("ftpOffsetPath").value,
      protocol: protocol,
    }
  } else {
    return false;
  }

  $.ajax({
      type: "PUT",
      url: "/shares/" + storageId.toString(),
      contentType: 'application/json',
      data: JSON.stringify(updateData),
      success: function (data, status, xhr) {
        if(data.ok) {
          $('#storage-name-'+storageId).text(storageName);
          $('#storage-protocol-'+storageId).text(protocol);
          $('#storage-state-'+storageId).text(updateData.state);
        }
      },
    error: function (xhrObj, error, reason) {
      console.log('Error while editing the share details: ', error);
    }
  });
}

function setStorageDetailsToBeDeleted(id, storageName) {
  var storageId = id.split('-')[1];
  document.getElementById("delete_storage_id").value = storageId;
  document.getElementById("delete_storage_name").value = storageName;
}

function deleteStorage() {
  var storageId = document.getElementById("delete_storage_id").value;

  $.ajax({
      type: "DELETE",
      url: "/shares/" + storageId.toString(),
      success: function (data, status, xhr) {
        var row = document.getElementById('storage-row-'+storageId);
        var table = document.getElementById('storageInfoLists');
        if(row && row.rowIndex) {
            table.deleteRow(row.rowIndex);
        }
      },
    error: function (xhrObj, error, reason) {
      console.log('Error while editing the share details: ', error);
    }
  });
}

/* API's to perform GET, PUT, POST, DELETE on Settings -> News Agency */
function createNewAgency() {
  var agencyId = document.getElementById("create_agency_id").value;
  var agencyName = document.getElementById("create_agency_name").value;
  var agencyDescription = document.getElementById("create_agency_description").value;
  var agencyFeedUrl = document.getElementById("create_agency_feed_url").value;
  var agencyFeedType = document.getElementById("create_agency_feed_type").value;
  var agencyFeedFormat = document.getElementById("create_agency_feed_format").value;

  var newData = {
    id: agencyId,
    name: agencyName,
    description: agencyDescription,
    config: {
      type: agencyFeedType,
      data_format: agencyFeedFormat,
      url: agencyFeedUrl,
    }
  };

  $.ajax({
    type: "POST",
    url: "/agencies",
    contentType: 'application/json',
    data: JSON.stringify(newData),
    success: function (data, status, xhr) {
      if (data.ok == true) {
        var row = '<tr id="agency-row-'+data._id+'" class="row">\
            <th id="agency-name-'+data._id+'" class="col-2">'+data.name+'</th>\
            <th id="agency-feed-type-'+data._id+'" class="col-2">'+data.type+'</th>\
            <th id="agency-feed-format-'+data._id+'" class="col-2">'+data.data_format+'</th>\
            <th id="agency-url-'+data._id+'" class="col-3">'+data.url+'</th>\
            <td class="col-3">\
              <button id=agency_edit-'+data._id+' class="table-edit" onclick="getAgencyInfoForUpdate(this.id)"  data-toggle="modal" data-target="#agency_edit_modal">Edit</button>\
              <button id=agency_delete-'+data._id+' name='+data.name+' onclick="setAgencyDetailsToBeDeleted(this.id, this.name)" class="table-del" data-toggle="modal" data-target="#agency_delete_modal">Delete</button>\
            </td>\
          </tr>'

        $('#agencyInfoLists tbody').append(row);

        document.getElementById("create_agency_id").value = '';
        document.getElementById("create_agency_name").value = '';
        document.getElementById("create_agency_description").value = '';
        document.getElementById("create_agency_feed_url").value = '';
      }
    },
    error: function (xhrObj, error, reason) {
      console.log('Error while editing the share details: ', error);
    }
  });
}

function getAgencyInfoForUpdate(id) {
  var agencyId = id.split('-')[1];

  $.ajax({
    type: "GET",
    url: "/agencies/" + agencyId.toString(),
    contentType: 'application/json',
    success: function (data, status, xhr) { 
          document.getElementById("edit_agency_id").value = data["_id"];
          document.getElementById("edit_agency_name").value = data.name;
          document.getElementById("edit_agency_description").value = data.description;
          document.getElementById("edit_agency_feed_url").value = data.config && data.config.url || '';
          document.getElementById("edit_agency_feed_type").value = data.config && data.config.type || '';
          document.getElementById("edit_agency_feed_format").value = data.config && data.config.data_format || '';
      },
    error: function (xhrObj, error, reason) { 
      console.log('Error while getting agency info: ', error);
    }
  });
}

function updateAgencyDetails() {
  var agencyId = document.getElementById("edit_agency_id").value;
  var agencyName = document.getElementById("edit_agency_name").value;
  var agencyDescription = document.getElementById("edit_agency_description").value;
  var agencyFeedUrl = document.getElementById("edit_agency_feed_url").value;
  var agencyFeedType = document.getElementById("edit_agency_feed_type").value;
  var agencyFeedFormat = document.getElementById("edit_agency_feed_format").value;

  var updateData = {
    name: agencyName,
    description: agencyDescription,
    config: {
      type: agencyFeedType,
      data_format: agencyFeedFormat,
      url: agencyFeedUrl,
    }
  };

  $.ajax({
    type: "PUT",
    url: "/agencies/" + agencyId.toString(),
    contentType: 'application/json',
    data: JSON.stringify(updateData),
    success: function (data, status, xhr) {
      $('#agency-name-'+agencyId).text(agencyName);
      $('#agency-feed-type-'+agencyId).text(agencyFeedType);
      $('#agency-feed-format-'+agencyId).text(agencyFeedFormat);
      $('#agency-url-'+agencyId).text(agencyFeedUrl);
    },
    error: function (xhrObj, error, reason) {
      console.log('Error while editing the share details: ', error);
    }
  });
}

function setAgencyDetailsToBeDeleted(id, agencyName) {
  var agencyId = id.split('-')[1];
  document.getElementById("delete_input_agency_id").value = agencyId;
  document.getElementById("delete_input_agency_name").value = agencyName;
}

function deleteAgency() {
  var agencyId = document.getElementById("delete_input_agency_id").value;

  $.ajax({
    type: "DELETE",
    url: "/agencies/" + agencyId.toString(),
    success: function (data, status, xhr) {
      var row = document.getElementById('agency-row-'+agencyId);
      var table = document.getElementById('agencyInfoLists');
      if(row && row.rowIndex) {
          table.deleteRow(row.rowIndex);
      }
    },
    error: function (xhrObj, error, reason) {
      console.log('Error while editing the share details: ', error);
    }
  });
}

function createNewEditor() {
  var editorId = document.getElementById("create_editor_id").value;
  var editorName = document.getElementById("create_editor_name").value;
  var editorIp = document.getElementById("create_editor_ip").value;
  var editorPort = document.getElementById("create_editor_port").value;
  var editorOffsetPath = document.getElementById("create_editor_offset_path").value;
  var editorUsername = document.getElementById("create_editor_username").value;
  var editorPassword = document.getElementById("create_editor_password").value;
  var editorProtocol = document.getElementById("create_editor_protocol").value;
  var editorFormat = $(".create_editor_format:checked").val();
  var editorUrl = document.getElementById('create_editor_url').value;

  var newData = {
    id: editorId,
    name: editorName,
    protocol: editorProtocol,
    data_format: editorFormat,
  };

  if(editorProtocol === 'upload') {
    newData.credentials = {
      ip: editorIp,
      port: editorPort,
      offset_path: editorOffsetPath,
      username: editorUsername,
      password: editorPassword
    };
  } else if(editorProtocol === 'post') {
    newData.credentials = {
      url: editorUrl,
    }
  } else {
    return false;
  }

  $.ajax({
    type: "POST",
    url: "/nrcs",
    contentType: 'application/json',
    data: JSON.stringify(newData),
    success: function (data, status, xhr) {
      if (data.ok == true) {
        var row = '<tr id="editor-row-'+data._id+'" class="row">\
            <th id="editor-name-'+data._id+'" class="col-3">'+data.name+'</th>\
            <th id="editor-protocol-'+data._id+'" class="col-3">'+data.protocol+'</th>\
            <th id="editor-data-format-'+data._id+'" class="col-3">'+data.data_format+'</th>\
            <td class="col-3">\
              <button id=editor_edit-'+data._id+' class="table-edit" onclick="getEditorInfoForUpdate(this.id)"  data-toggle="modal" data-target="#editor_edit_modal">Edit</button>\
              <button id=editor_del-'+data._id+' name="'+data.name+'" onclick="setEditorDetailsToBeDeleted(this.id, this.name)" class="table-del" data-toggle="modal" data-target="#editor_delete_modal">Delete</button>\
            </td>\
          </tr>';

        $('#editorInfoLists tbody').append(row);

        document.getElementById("create_editor_id").value = '';
        document.getElementById("create_editor_name").value = '';
        document.getElementById("create_editor_ip").value = '';
        document.getElementById("create_editor_port").value = '';
        document.getElementById("create_editor_offset_path").value = '';
        document.getElementById("create_editor_username").value = '';
        document.getElementById("create_editor_password").value = '';
        document.getElementById('create_editor_url').value = '';
      }
    },
    error: function (xhrObj, error, reason) {
      console.log('Error while creating the editor: ', error);
    }
  });
}

function getEditorInfoForUpdate(editorId) {
  var editorID = editorId.split('-')[1];

  $.ajax({
    type: "GET",
    url: "/nrcs/" + editorID.toString(),
    contentType: 'application/json',
    success: function (editorData, status, xhr) {
      console.log(editorData);
      if (editorData) {
        var protocol = editorData.protocol;

        document.getElementById("edit_editor_id").value = editorData['_id'];
        document.getElementById("edit_editor_name").value = editorData.name;

        if (protocol === 'post') {
          $('#edit_editor_protocol').val(protocol);
          $('#editor_edit_modal .box').hide();
          $('#'+protocol+'_editor_edit_box').show();
          document.getElementById("edit_editor_url").value = editorData.credentials.url;
        } else if (protocol === 'upload') {
          $('#edit_editor_protocol').val(protocol);
          $('#editor_edit_modal .box').hide();
          $('#'+protocol+'_editor_edit_box').show();

          document.getElementById("edit_editor_ip").value = editorData.credentials.ip;
          document.getElementById("edit_editor_port").value = editorData.credentials.port;
          document.getElementById("edit_editor_offset_path").value = editorData.credentials.offset_path;
          document.getElementById("edit_editor_username").value = editorData.credentials.username;
          document.getElementById("edit_editor_password").value = editorData.credentials.password;
        }

        $(".edit_editor_format[value='"+editorData.data_format+"']").prop("checked", true);
      }
    },
    error: function (xhrObj, error, reason) { 
      console.log('Error while getting editor info: ', error);
    }
  });
}

function updateEditorDetails() {
  var editorId = document.getElementById("edit_editor_id").value;
  var editorName = document.getElementById("edit_editor_name").value;
  var editorIp = document.getElementById("edit_editor_ip").value;
  var editorPort = document.getElementById("edit_editor_port").value;
  var editorOffsetPath = document.getElementById("edit_editor_offset_path").value;
  var editorUsername = document.getElementById("edit_editor_username").value;
  var editorPassword = document.getElementById("edit_editor_password").value;
  var editorProtocol = document.getElementById("edit_editor_protocol").value;
  var editorFormat = $(".edit_editor_format:checked").val();
  var editorUrl = document.getElementById('edit_editor_url').value;

  var updatedData = {
    id: editorId,
    name: editorName,
    protocol: editorProtocol,
    data_format: editorFormat,
  };

  if(editorProtocol === 'upload') {
    updatedData.credentials = {
      ip: editorIp,
      port: editorPort,
      offset_path: editorOffsetPath,
      username: editorUsername,
      password: editorPassword
    };
  } else if(editorProtocol === 'post') {
    updatedData.credentials = {
      url: editorUrl,
    }
  } else {
    return false;
  }

  $.ajax({
    type: "PUT",
    url: "/nrcs/"+ editorId.toString(),
    contentType: 'application/json',
    data: JSON.stringify(updatedData),
    success: function (data, status, xhr) {
      $('#editor-name-'+editorId).text(editorName);
      $('#editor-protocol-'+editorId).text(editorProtocol);
      $('#editor-data-format-'+editorId).text(editorFormat);

      document.getElementById("edit_editor_id").value = '';
      document.getElementById("edit_editor_name").value = '';
      document.getElementById("edit_editor_ip").value = '';
      document.getElementById("edit_editor_port").value = '';
      document.getElementById("edit_editor_offset_path").value = '';
      document.getElementById("edit_editor_username").value = '';
      document.getElementById("edit_editor_password").value = '';
      document.getElementById('edit_editor_url').value = '';
    },
    error: function (xhrObj, error, reason) {
      console.log('Error while editing the editor details: ', error);
    }
  });
}

function setEditorDetailsToBeDeleted(editorId, editorName) {
  var id = editorId.split('-')[1];
  document.getElementById("delete_input_editor_id").value = id;
  document.getElementById("delete_input_editor_name").value = editorName;
}

function deleteEditor() {
  var editorId = document.getElementById("delete_input_editor_id").value;

  $.ajax({
    type: "DELETE",
    url: "/nrcs/" + editorId.toString(),
    success: function (data, status, xhr) {
      var row = document.getElementById('editor-row-'+editorId);
      var table = document.getElementById('editorInfoLists');
      if(row && row.rowIndex) {
          table.deleteRow(row.rowIndex);
      }
    },
    error: function (xhrObj, error, reason) {
      console.log('Error while deleting editor: ', error);
    }
  });
}