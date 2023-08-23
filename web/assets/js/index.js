function alledit() {
    document.querySelector("#user_input").value = 
                document.querySelector("#display").innerHTML;
}
function allsave() {
    document.querySelector("#display").innerHTML = 
                document.querySelector("#user_input").value;
}


function gettitle(){
    let newtitles = document.getElementById("modal-title-textarea").value;
    if (newtitles !== ""){
    let dems = document.getElementById("appended-tiltle");
    dems.innerHTML += newtitles+"<br>";
    document.getElementById("modal-title-textarea").value = "";
    }
};
function getdes(){
    let newdes = document.getElementById("modal-title-des").value;
    if (newdes !== ""){
    let des = document.getElementById("appended-des");
    des.innerHTML += newdes+"<br>";
    document.getElementById("modal-title-des").value = "";
    }
};



/* dropdown content change */
$(document).ready(function(){
    $("select").change(function(){
        $(this).find("option:selected").each(function(){
            var optionValue = $(this).attr("value");
            if(optionValue){
                $(".box").not("." + optionValue).hide();
                $("." + optionValue).show();
            } else{
                $(".box").hide();
            }
        });
    }).change();
});


/* setting tabs */
function openCity(evt, cityName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(cityName).style.display = "block";
    evt.currentTarget.className += " active";
}
/* golive tabs */
function openTV(evt, cityName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(cityName).style.display = "block";
    evt.currentTarget.className += " active";
}

/* loading stories on basis of agency id */
function loadAgencyStoryFeed(agencyId) {
    console.log("loadAgencyStoryFeed: agencyId: ", agencyId)
    window.location.href = "/pages/index?agency_id="+agencyId
}

function openStreamTab(streamName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    window.location.href = "/pages/golive?stream_name="+streamName
}

function playStream(streamUrl){
    var video = document.getElementById('stream-video-player');
    if(Hls.isSupported()) {
        var hls = new Hls();
        hls.loadSource(streamUrl);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED,function() {
            video.play();
        });
    }
    else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = streamUrl;
        video.addEventListener('loadedmetadata',function() {
            video.play();
        });
    }
}