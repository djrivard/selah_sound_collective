(function(){
  var audio=document.getElementById('audio');
  var PLAY='M8 5v14l11-7z', PAUSE='M6 5h4v14H6zM14 5h4v14h-4z';
  var heroBtn=document.getElementById('heroPlay'),heroIcon=document.getElementById('heroIcon'),heroLabel=document.getElementById('heroLabel');
  var nbPlay=document.getElementById('nbPlay'),nbIcon=document.getElementById('nbIcon'),nowbar=document.getElementById('nowbar');
  var ctaPlay=document.getElementById('ctaPlay'),ctaText=document.getElementById('ctaText');
  var track=document.getElementById('track'),fill=document.getElementById('fill'),knob=document.getElementById('knob');
  var tCur=document.getElementById('tCur'),tDur=document.getElementById('tDur');

  function fmt(s){if(!isFinite(s))return'0:00';s=Math.floor(s);return Math.floor(s/60)+':'+('0'+(s%60)).slice(-2);}
  function setIcons(p){var d=p?PAUSE:PLAY;heroIcon.setAttribute('d',d);nbIcon.setAttribute('d',d);heroBtn.classList.toggle('is-playing',p);heroLabel.textContent=p?'Now Playing':'Play the Song';ctaText.textContent=p?'Pause':'Play the Song';}
  function toggle(){if(audio.paused){var pr=audio.play();if(pr&&pr.catch)pr.catch(function(){heroLabel.textContent='Tap again to play';});}else audio.pause();}

  heroBtn.addEventListener('click',toggle);
  nbPlay.addEventListener('click',toggle);
  ctaPlay.addEventListener('click',toggle);

  audio.addEventListener('play',function(){setIcons(true);nowbar.classList.add('show');cols.classList.add('syncing');document.getElementById('syncHint').classList.add('on');});
  audio.addEventListener('pause',function(){setIcons(false);});
  audio.addEventListener('loadedmetadata',function(){tDur.textContent=fmt(audio.duration);});
  audio.addEventListener('timeupdate',function(){var pct=audio.duration?audio.currentTime/audio.duration*100:0;fill.style.width=pct+'%';knob.style.left=pct+'%';tCur.textContent=fmt(audio.currentTime);syncTick();});
  audio.addEventListener('ended',function(){setIcons(false);});

  function seek(x){var r=track.getBoundingClientRect();var p=Math.min(1,Math.max(0,(x-r.left)/r.width));if(audio.duration)audio.currentTime=p*audio.duration;}
  var drag=false;
  track.addEventListener('mousedown',function(e){drag=true;seek(e.clientX);});
  window.addEventListener('mousemove',function(e){if(drag)seek(e.clientX);});
  window.addEventListener('mouseup',function(){drag=false;});
  track.addEventListener('touchstart',function(e){seek(e.touches[0].clientX);},{passive:true});
  track.addEventListener('touchmove',function(e){seek(e.touches[0].clientX);},{passive:true});

  window.addEventListener('keydown',function(e){if(e.code==='Space'&&!/INPUT|TEXTAREA|BUTTON|A/.test(document.activeElement.tagName)){e.preventDefault();toggle();}});

  new IntersectionObserver(function(en){if(!en[0].isIntersecting)nowbar.classList.add('show');},{threshold:0}).observe(document.querySelector('.hero'));

  /* reveal lyric sections */
  var io=new IntersectionObserver(function(en){en.forEach(function(x){if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target);}});},{threshold:.18});
  document.querySelectorAll('.section,.whisper').forEach(function(el){io.observe(el);});

  /* ---------- line-by-line sync (estimated timestamps, scaled to true length) ---------- */
  var cols=document.getElementById('cols');
  var lines=[].slice.call(document.querySelectorAll('.ln'));
  var scale=1, curIdx=-1, lastScroll=0, lyricsInView=false;
  window.addEventListener('scroll',function(){lastScroll=Date.now();},{passive:true});
  new IntersectionObserver(function(e){lyricsInView=e[0].isIntersecting;},{threshold:.04}).observe(document.querySelector('.lyrics-wrap'));
  function syncTick(){
    var ct=audio.currentTime, idx=-1;
    for(var i=0;i<lines.length;i++){ if(parseFloat(lines[i].dataset.t)*scale<=ct+0.25) idx=i; else break; }
    if(idx!==curIdx){
      if(curIdx>=0&&lines[curIdx])lines[curIdx].classList.remove('active');
      curIdx=idx;
      if(idx>=0){
        lines[idx].classList.add('active');
        if(!audio.paused&&lyricsInView&&(Date.now()-lastScroll>2800)){
          lines[idx].scrollIntoView({block:'center',behavior:'smooth'});
        }
      }
    }
  }

  /* ---------- share ---------- */
  var pageUrl=location.href.split('#')[0];
  var meta=window.SELAH_SONG||{};
  var songTitle=meta.title||document.title;
  var shareText=meta.shareText||songTitle;
  document.getElementById('shareX').href='https://twitter.com/intent/tweet?text='+encodeURIComponent(shareText)+'&url='+encodeURIComponent(pageUrl);
  document.getElementById('shareFb').href='https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(pageUrl);
  document.getElementById('shareMail').href='mailto:?subject='+encodeURIComponent(songTitle)+'&body='+encodeURIComponent(shareText+'\n\n'+pageUrl);
  var toast=document.getElementById('toast');
  function showToast(m){toast.textContent=m;toast.classList.add('show');setTimeout(function(){toast.classList.remove('show');},1900);}
  document.getElementById('shareNative').addEventListener('click',function(){
    if(navigator.share){navigator.share({title:songTitle,text:shareText,url:pageUrl}).catch(function(){});}
    else if(navigator.clipboard){navigator.clipboard.writeText(pageUrl).then(function(){showToast('Link copied');});}
    else showToast(pageUrl);
  });

  /* ---------- fit band name within the cover frame ---------- */
  function fitBand(){
    var el=document.getElementById('coverBand'); if(!el)return;
    el.style.letterSpacing='0.34em'; el.style.fontSize='13px';
    var ls=0.34, fs=13;
    while(el.scrollWidth>el.clientWidth&&ls>0.06){ls-=0.02;el.style.letterSpacing=ls.toFixed(2)+'em';}
    while(el.scrollWidth>el.clientWidth&&fs>8){fs-=0.5;el.style.fontSize=fs+'px';}
  }
  fitBand(); window.addEventListener('resize',fitBand);
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fitBand);

  /* ---------- visualizer ---------- */
  var canvas=document.getElementById('viz'),ctx=canvas.getContext('2d');
  var dpr=Math.min(window.devicePixelRatio||1,2);
  function rs(){canvas.width=innerWidth*dpr;canvas.height=160*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);}
  rs();window.addEventListener('resize',rs);
  var BINS=52,ph=[],sp=[];for(var b=0;b<BINS;b++){ph.push(Math.random()*6.28);sp.push(.9+Math.random()*1.7);}
  var lvl=0,tt=0;
  function draw(){
    requestAnimationFrame(draw);
    var W=innerWidth,H=160;ctx.clearRect(0,0,W,H);
    var playing=!audio.paused;
    lvl+=((playing?1:0)-lvl)*0.05; tt+=playing?0.045:0.012;
    var bw=W/BINS;
    function hAt(i){var env=.45+.55*Math.sin(Math.PI*(i+.5)/BINS);var s=.55+.45*Math.sin(tt*sp[i]+ph[i])+.18*Math.sin(tt*.6+i*.4);s=Math.max(0,Math.min(1.3,s));var base=env*s*112;var idle=8+4*Math.sin(tt*.8+i*.5);return Math.max(2,base*lvl+idle*(1-lvl));}
    var g=ctx.createLinearGradient(0,H,0,0);g.addColorStop(0,'rgba(201,164,70,0.5)');g.addColorStop(1,'rgba(201,164,70,0)');ctx.fillStyle=g;
    ctx.beginPath();ctx.moveTo(0,H);for(var j=0;j<BINS;j++)ctx.lineTo(j*bw+bw/2,H-hAt(j));ctx.lineTo(W,H);ctx.closePath();ctx.fill();
    ctx.beginPath();for(var k=0;k<BINS;k++){var x=k*bw+bw/2,y=H-hAt(k);if(k===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}
    ctx.strokeStyle='rgba(224,189,99,'+(.4+.45*lvl)+')';ctx.lineWidth=1.6;ctx.shadowColor='rgba(201,164,70,.9)';ctx.shadowBlur=8+10*lvl;ctx.stroke();ctx.shadowBlur=0;
  }
  draw();
})();
