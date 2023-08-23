// ApiRequest communicates to JournoApi and call handler Callback functions on getting response
function ApiRequest (requestType, requestClass, store = null) {
	this.requestType = requestType;
	this.requestClass = requestClass
	this.store = store;
}

ApiRequest.prototype.onSuccess = function (data, status, xhr) {
	var resp = {
	    "data": data,
	    "status": Constants.SUCCESS,
	    "store": this.store,
	    "type": this.requestType,
	    "class": this.requestClass
	};

	// Calling response handler
	HandleApiResponse(resp);
};

ApiRequest.prototype.onFailure = function (xhrObj, error, reason) {
	var resp = {
	    "data": null,
	    "status": Constants.FAILED,
	    "store": this.store,
	    "type": this.requestType,
	    "class": this.requestClass,
	    "reason": reason,
	    "responseText": xhrObj.responseText
	};

	// Calling response handler
	HandleApiResponse(resp);
};

// ----------------------- storage -------------------------
function getStorageInfo(storageId, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_GET, Constants.REQUEST_CLASS_STORAGE, store);
	$.ajax({
    	type: "GET",
    	url: "/shares/" + storageId.toString(),
    	contentType: 'application/json',
    	success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
};

function updateStorageInfo(storageId, data, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_PUT, Constants.REQUEST_CLASS_STORAGE, store)
    $.ajax({
        type: "PUT",
        url: "/shares/" + storageId.toString(),
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

function insertStorageInfo(data, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_POST, Constants.REQUEST_CLASS_STORAGE, store)
    $.ajax({
        type: "POST",
        url: "/shares",
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

function deleteStorageInfo(storageId, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_DELETE, Constants.REQUEST_CLASS_STORAGE, store)
    $.ajax({
        type: "DELETE",
        url: "/shares/" + storageId.toString(),
        contentType: 'application/json',
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

// ----------------------- agencies --------------------------
function getAgencyInfo(agencyId, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_GET, Constants.REQUEST_CLASS_AGENCY, store);
	$.ajax({
    	type: "GET",
    	url: "/agencies/" + agencyId.toString(),
    	contentType: 'application/json',
    	success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
};

function updateAgencyInfo(agencyId, data, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_PUT, Constants.REQUEST_CLASS_AGENCY, store)
    $.ajax({
        type: "PUT",
        url: "/agencies/" + agencyId.toString(),
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

function insertAgencyInfo(data, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_POST, Constants.REQUEST_CLASS_AGENCY, store)
    $.ajax({
        type: "POST",
        url: "/agencies",
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

function deleteAgencyInfo(agencyId, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_DELETE, Constants.REQUEST_CLASS_AGENCY, store)
    $.ajax({
        type: "DELETE",
        url: "/agencies/" + agencyId.toString(),
        contentType: 'application/json',
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

// ----------------------- categories --------------------------
function getCategoryInfo(categoryId, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_GET, Constants.REQUEST_CLASS_CATEGORY, store);
	$.ajax({
    	type: "GET",
    	url: "/categories/" + categoryId.toString(),
    	contentType: 'application/json',
    	success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
};

function updateCategoryInfo(categoryId, data, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_PUT, Constants.REQUEST_CLASS_CATEGORY, store)
    $.ajax({
        type: "PUT",
        url: "/categories/" + categoryId.toString(),
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

function insertCategoryInfo(data, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_POST, Constants.REQUEST_CLASS_CATEGORY, store)
    $.ajax({
        type: "POST",
        url: "/categories",
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

function deleteCategoryInfo(categoryId, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_DELETE, Constants.REQUEST_CLASS_CATEGORY, store)
    $.ajax({
        type: "DELETE",
        url: "/categories/" + categoryId.toString(),
        contentType: 'application/json',
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

// ----------------------- editor apps --------------------------
function getEditorAppInfo(appId, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_GET, Constants.REQUEST_CLASS_EDITOR_APP, store);
	$.ajax({
    	type: "GET",
    	url: "/nrcs/" + appId.toString(),
    	contentType: 'application/json',
    	success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
};

function updateEditorAppInfo(appId, data, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_PUT, Constants.REQUEST_CLASS_EDITOR_APP, store)
    $.ajax({
        type: "PUT",
        url: "/nrcs/" + appId.toString(),
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

function insertEditorAppInfo(data, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_POST, Constants.REQUEST_CLASS_EDITOR_APP, store)
    $.ajax({
        type: "POST",
        url: "/nrcs",
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}

function deleteEditorAppInfo(appId, store = null) {
    var req = new ApiRequest(Constants.REQUEST_TYPE_DELETE, Constants.REQUEST_CLASS_EDITOR_APP, store)
    $.ajax({
        type: "DELETE",
        url: "/nrcs/" + appId.toString(),
        contentType: 'application/json',
        success: function (data, status, xhr) { req.onSuccess(data, status, xhr);},
    	error: function (xhrObj, error, reason) { req.onFailure(xhrObj, error, reason);}
    });
}