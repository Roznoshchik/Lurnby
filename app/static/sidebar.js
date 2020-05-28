$(document).ready(function() {
    
    // add img-fluid class to all images
    var list;
    list = document.querySelectorAll("img");
    for (var i = 0; i < list.length; ++i) {
      list[i].classList.add('img-fluid');
    }
  });

  var content = document.getElementById('content');

  var currTextSize = 16;
  var currlineheight = 24;
  var currleft = 8;
  var currright = 8;

  content.style.fontSize = currTextSize + 'px';

  function bigtext () {
  ++currTextSize;
  content.style.fontSize = currTextSize + 'px';
  }
  function biglineheight () {
  ++currlineheight;
  content.style.lineHeight = currlineheight + 'px';
  }
  function bigmargin () {
  currleft += 8;
  currright += 8;
  content.style.marginLeft = currleft + 'px';
  content.style.marginRight = currright + 'px';

  }


  function smalltext () {
  --currTextSize;
  content.style.fontSize = currTextSize + 'px';
  }
  function smalllineheight () {
  --currlineheight;
  content.style.lineHeight = currlineheight + 'px';
  }
  function smallmargin () {
  currleft -= 8;
  currright -= 8;
  content.style.marginLeft = currleft + 'px';
  content.style.marginRight = currright + 'px';

  }


  $('#sidebar-collapse').on('click', function() {
    var sidebar = document.getElementById("sidebar");
    var standard = document.getElementById("standard");


    if (sidebar.style.width === "48px"){
      sidebar.style.width = "300px";
      standard.style.marginLeft = "300px";
      sidebar.style.background = "#EBC354"

    }
    else{
      sidebar.style.width = "48px";
      standard.style.marginLeft = "48px";
      sidebar.style.background = "none"
    }

    var x = document.getElementById("inviz");
    if (x.style.display === "none") {
      x.style.display = "inline";
    } 
    else {
      x.style.display = "none";
    }

    if($("#collapse-icon").attr('class') == "fa fa-angle-double-right"){
      $("#collapse-icon").attr('class', 'fa fa-angle-double-left');
    }
    else{
      $("#collapse-icon").attr('class', "fa fa-angle-double-right");
    }
     
    var sidebarContent = document.getElementsByClassName("sidebar-content");
    if (sidebarContent[0].style.display === "none") {
      sidebarContent[0].style.display = "block";
    } 
    else {
      sidebarContent[0].style.display = "none";
    }


  });


  $('#sidebarcollapse').on('click', function () {

    var x = document.getElementById("inviz");
    if (x.style.display === "none") {
      x.style.display = "inline";
    } 
    else {
      x.style.display = "none";
    }

    $('#sidebar').toggleClass('active');
    $('#sidebarcollapse').toggleClass('slide-left settings-button-left');


    if($("#collapse-icon").attr('class') == "fa fa-angle-double-right"){
      $("#collapse-icon").attr('class', 'fa fa-angle-double-left');
    }
    else{
      $("#collapse-icon").attr('class', "fa fa-angle-double-right");
    }
  });     

  
  $('#make-sepia').on('click', function () {
    document.body.classList.remove("dark-mode");
    document.getElementById("make-dark").classList.remove("activebutton");
    document.body.classList.remove("light-mode");
    document.getElementById("make-light").classList.remove("activebutton");
    document.body.classList.add("sepia-mode");
    $('#make-sepia').attr('class', "activebutton");

  
  });

  $('#make-light').on('click', function () {
    document.body.classList.remove("sepia-mode");
    document.getElementById("make-sepia").classList.remove("activebutton");
    document.body.classList.remove("dark-mode");
    document.getElementById("make-dark").classList.remove("activebutton");
    document.body.classList.add("light-mode");
    $('#make-light').attr('class', "activebutton");

  });
  
  $('#make-dark').on('click', function () {
    document.body.classList.remove("sepia-mode");
    document.getElementById("make-sepia").classList.remove("activebutton");
    document.body.classList.remove("light-mode");
    document.getElementById("make-light").classList.remove("activebutton");
    document.body.classList.add("dark-mode");
    $('#make-dark').attr('class', "activebutton");      
  });
  
  $('#make-sans').on('click', function () {
    document.getElementById("content").classList.remove("serif-mode");
    document.getElementById("content").classList.add("sans-mode");
  });  

  $('#make-serif').on('click', function () {
    document.getElementById("content").classList.remove("sans-mode");
    document.getElementById("content").classList.add("serif-mode");
  });  

  $('#p-less').on('click', function () {
    smalltext();       
  });  
  $('#p-more').on('click', function () {
    bigtext();
  });
  $('#lheight-less').on('click', function () {
    smalllineheight();       
  });  
  $('#lheight-more').on('click', function () {
    biglineheight();
  });    
  $('#margin-less').on('click', function () {
    smallmargin();       
  });  
  $('#margin-more').on('click', function () {
    bigmargin();
  }); 