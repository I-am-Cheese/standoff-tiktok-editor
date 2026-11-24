#!/usr/bin/env python3
"""Prepare an FCP XML and explicit Premiere Pro 2024 import script; never launch Adobe."""
import argparse
import json
import math
import re
import sys
import uuid
from pathlib import Path
import xml.etree.ElementTree as ET


def build(plan_path, output_dir, export_preset=None):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    output_dir = Path(output_dir).resolve()
    fps = plan.get("fps", 60)
    if fps != 60:
        raise ValueError("Premiere template requires fps=60")
    total, intro = int(plan["total_frames"]), int(plan["intro_frames"])
    game = total - intro
    fade = float(plan.get("fade_seconds", 2.814375))
    if not 0 < intro < total or not math.isfinite(fade) or not 0 < fade <= game / fps:
        raise ValueError("Require 0 < intro_frames < total_frames and a fade within gameplay")

    def path(value):
        p = Path(value)
        p = (plan_path.parent / p).resolve() if not p.is_absolute() else p.resolve()
        if not p.is_file():
            raise ValueError("Media file does not exist: " + str(p))
        return p

    montage, overlay, audio = [path(plan[k]) for k in ("montage_source", "chad_overlay", "audio")]
    extras = {k: [str(path(p)) for p in plan.get(k, [])] for k in ("sources", "graphics", "references")}
    logos = [(path(r["path"]), int(r["start_frame"]), int(r["end_frame"])) for r in plan["logo_steps"]]
    shots = []
    cursor = 0
    for i, r in enumerate(plan["shots"]):
        a, b = int(r["start_frame"]), int(r["end_frame"])
        si, so = int(r.get("source_in_frame", a)), int(r.get("source_out_frame", b))
        if a != cursor or b <= a or b > game or si < 0 or so - si != b - a:
            raise ValueError("Shot %d must be contiguous, within gameplay, and have matching source duration" % (i + 1))
        shots.append((a, b, si, so, str(r.get("source_label", "CUT %03d" % (i + 1)))))
        cursor = b
    if cursor != game or not shots:
        raise ValueError("Shots must cover every gameplay frame")
    cursor = 0
    for _, a, b in logos:
        if a != cursor or b <= a or b > intro:
            raise ValueError("Logo steps must cover intro contiguously")
        cursor = b
    if cursor != intro:
        raise ValueError("Logo steps must cover every intro frame")
    if len({r[2] for r in shots}) != len(shots):
        raise ValueError("Every shot must have a distinct source in-point")
    title = str(plan.get("title", "Vertical edit"))
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .") or "Vertical edit"
    native = output_dir / (stem + ".prproj")
    xml_path, jsx_path = output_dir / "timeline.xml", output_dir / "import.jsx"
    preset = path(export_preset) if export_preset else None
    export_path = output_dir / (stem + ".mp4")
    for p in (native, xml_path, jsx_path, *([export_path] if preset else [])):
        if p.exists():
            raise ValueError("Refusing to overwrite existing output: " + str(p))

    def el(parent, tag, value=None, **attrs):
        node = ET.SubElement(parent, tag, attrs)
        if value is not None:
            node.text = str(value)
        return node

    def rate(parent):
        r = el(parent, "rate")
        el(r, "timebase", fps)
        el(r, "ntsc", "FALSE")

    def dimensions(parent, w, h):
        rate(parent)
        for k, v in (("width", w), ("height", h), ("anamorphic", "FALSE"), ("pixelaspectratio", "square"), ("fielddominance", "none")):
            el(parent, k, v)

    def sequence(name, uid, duration, height):
        s = ET.Element("sequence", id=uid)
        el(s, "name", name)
        el(s, "duration", duration)
        rate(s)
        m = el(s, "media")
        v, a = el(m, "video"), el(m, "audio")
        dimensions(el(el(v, "format"), "samplecharacteristics"), 720, height)
        sc = el(el(a, "format"), "samplecharacteristics")
        el(sc, "depth", 16)
        el(sc, "samplerate", 48000)
        return s, v, a

    count = 0
    seen = set()

    def clip(track, name, a, b, media=None, height=1280, nested=None, sound=False, si=0, file_id=None, file_duration=None):
        nonlocal count
        count += 1
        c = el(track, "clipitem", id="clip-%d" % count)
        el(c, "name", name)
        el(c, "enabled", "TRUE")
        el(c, "duration", b-a)
        rate(c)
        for k, val in (("start", a), ("end", b), ("in", si), ("out", si+b-a)):
            el(c, k, val)
        if nested is not None:
            c.append(nested)
        else:
            fid = file_id or "file-%d" % count
            f = el(c, "file", id=fid)
            if fid not in seen:
                seen.add(fid)
                el(f, "name", media.name)
                el(f, "pathurl", media.as_uri())
                rate(f)
                el(f, "duration", file_duration or si+b-a)
                m = el(f, "media")
                if sound:
                    au = el(m, "audio")
                    sc = el(au, "samplecharacteristics")
                    el(sc, "depth", 16)
                    el(sc, "samplerate", 48000)
                    el(au, "channelcount", 2)
                else:
                    v = el(m, "video")
                    dimensions(el(v, "samplecharacteristics"), 720, height)
                    if media.suffix.lower() == ".png":
                        el(v, "stillframe", "TRUE")
            if media.suffix.lower() == ".png":
                el(c, "alphatype", "straight")
        st = el(c, "sourcetrack")
        el(st, "mediatype", "audio" if sound else "video")
        el(st, "trackindex", 1)
        return c

    intro_seq, iv, _ = sequence("01 INTRO", "intro", intro, 1280)
    tr = el(iv, "track")
    for p, a, b in logos:
        clip(tr, p.stem, a, b, p)
    game_seq, gv, _ = sequence("02 GAMEPLAY", "gameplay", game, 732)
    tr = el(gv, "track")
    for a, b, si, so, label in shots:
        clip(tr, label, a, b, montage, height=732, si=si, file_id="montage-source", file_duration=max(s[3] for s in shots))
    clip(el(gv, "track"), "CHAD", 0, game, overlay, height=732)
    main, mv, ma = sequence("MAIN - " + title, "main", total, 1280)
    clip(el(mv, "track"), "BACKGROUND - SAME GAMEPLAY", intro, total, nested=game_seq)
    tr = el(mv, "track")
    clip(tr, "INTRO", 0, intro, nested=intro_seq)
    clip(tr, "GAMEPLAY", intro, total, nested=ET.Element("sequence", id="gameplay"))
    clip(el(ma, "track"), "MUSIC - TRIMMED AND FADED", 0, total, audio, sound=True)
    root = ET.Element("xmeml", version="5")
    root.append(main)
    config = dict(xml=str(xml_path), output=str(native), scratch=str(output_dir / ("scratch-" + uuid.uuid4().hex + ".prproj")), log=str(output_dir / "import.log"), game_frames=game, fade=fade, fps=fps, montage=str(montage), audio=str(audio), overlay=str(overlay), logo_paths=[str(p) for p, _, _ in logos], export_preset=str(preset) if preset else None, export_path=str(export_path), **extras)
    output_dir.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
    jsx_path.write_text("// Generated configuration is JSON, never textual token substitution.\nvar cfg = " + json.dumps(config, ensure_ascii=True) + ";\n" + JSX, encoding="utf-8")
    return xml_path, jsx_path


JSX = r'''
var log = new File(cfg.log);
log.encoding = "UTF-8"; log.open("w");
function say(s) { log.writeln(s); }
function same(a,b) { return a.replace(/\\/g,"/").toLowerCase() === b.replace(/\\/g,"/").toLowerCase(); }
function has(paths,p) { for(var i=0;i<paths.length;i++) if(same(paths[i],p)) return true; return false; }
function intrinsic(c,name) {
 for(var i=0;i<c.components.numItems;i++) { var v=c.components[i]; if(v.matchName==="AE.ADBE "+name || v.displayName===name) return v; }
 throw Error("Missing intrinsic component: "+name);
}
function collect(bin,out) {
 for(var i=0;i<bin.children.numItems;i++) { var p=bin.children[i]; if(p.type===2) collect(p,out); else out.push(p); }
}
try {
 if(new File(cfg.output).exists || new File(cfg.scratch).exists) throw Error("Project output or scratch already exists; rebuild in a fresh directory");
 if(cfg.export_preset && new File(cfg.export_path).exists) throw Error("Export output already exists");
 app.newProject(cfg.scratch);
 if(!app.project.importFiles([cfg.xml],true,app.project.rootItem,false)) throw Error("XML import failed");
 var root=app.project.rootItem, bins={}, labels=["01 Subsequences","02 Sources","03 Graphics","04 Music","05 References","06 Prepared clips"];
 for(var i=0;i<labels.length;i++) bins[labels[i]]=root.createBin(labels[i]);
 var main=null;
 if(app.project.sequences.numSequences!==3) throw Error("Expected three imported sequences");
 for(var i=0;i<app.project.sequences.numSequences;i++) {
  var sq=app.project.sequences[i];
  if(sq.name.indexOf("MAIN - ")===0) { main=sq; sq.projectItem.moveBin(root); }
  else sq.projectItem.moveBin(bins["01 Subsequences"]);
 }
 if(!main) throw Error("MAIN sequence missing");
 app.project.openSequence(main.sequenceID);
 var bg=main.videoTracks[0].clips[0], fg=main.videoTracks[1].clips[1];
 intrinsic(bg,"Motion").properties[1].setValue(1280/732*100,true);
 app.enableQE();
 var effect=qe.project.getVideoEffectByName("Gaussian Blur");
 if(!effect) throw Error("Gaussian Blur unavailable; use Premiere's English effect name or adapt for localization");
 var qt=qe.project.getActiveSequence().getVideoTrackAt(0), added=false;
 for(var i=0;i<qt.numItems;i++) { var item=qt.getItemAt(i); if(item.type==="Clip") { item.addVideoEffect(effect); added=true; break; } }
 if(!added) throw Error("Background effect target missing");
 var found=false;
 for(var i=0;i<bg.components.numItems;i++) {
  var comp=bg.components[i];
  if(comp.matchName==="AE.ADBE Gaussian Blur 2" || comp.displayName==="Gaussian Blur") {
   if(comp.properties.numItems<3) throw Error("Unexpected Gaussian Blur property layout");
   comp.properties[0].setValue(52,true); comp.properties[2].setValue(true,true); found=true;
  }
 }
 if(!found) throw Error("Gaussian Blur attachment failed");
 var layers=[bg,fg];
 for(var i=0;i<layers.length;i++) {
  var c=layers[i],op=intrinsic(c,"Opacity").properties[0]; op.setTimeVarying(true);
  var a=new Time(),b=new Time();
  a.seconds=c.inPoint.seconds+cfg.game_frames/cfg.fps-cfg.fade;
  b.seconds=c.inPoint.seconds+cfg.game_frames/cfg.fps-1/cfg.fps;
  op.addKey(a); op.setValueAtKey(a,100,true); op.addKey(b); op.setValueAtKey(b,0,true);
 }
 var leaves=[]; collect(root,leaves);
 for(var i=0;i<leaves.length;i++) {
  var p=leaves[i],path=p.getMediaPath(); if(!path) continue;
  if(p.isOffline()) throw Error("Offline media: "+path);
  if(same(path,cfg.montage)) p.moveBin(bins["06 Prepared clips"]);
  else if(same(path,cfg.audio)) p.moveBin(bins["04 Music"]);
  else if(same(path,cfg.overlay) || has(cfg.logo_paths,path)) p.moveBin(bins["03 Graphics"]);
 }
 var imports=[[cfg.sources,"02 Sources"],[cfg.graphics,"03 Graphics"],[cfg.references,"05 References"]];
 for(var i=0;i<imports.length;i++) if(imports[i][0].length && !app.project.importFiles(imports[i][0],true,bins[imports[i][1]],false)) throw Error("Extra media import failed: "+imports[i][1]);
 leaves=[]; collect(root,leaves);
 for(var i=0;i<leaves.length;i++) if(leaves[i].getMediaPath() && leaves[i].isOffline()) throw Error("Offline imported media: "+leaves[i].name);
 app.project.openSequence(main.sequenceID);
 if(new File(cfg.output).exists) throw Error("Project output appeared during import; refusing overwrite");
 app.project.saveAs(cfg.output);
 if(!new File(cfg.output).exists) throw Error("Project save failed");
 say("SAVED "+cfg.output);
 if(cfg.export_preset) {
  if(new File(cfg.export_path).exists) throw Error("Export output appeared during import; refusing overwrite");
  var result=main.exportAsMediaDirect(cfg.export_path,cfg.export_preset,0);
  say("EXPORT result="+result+" path="+cfg.export_path);
 }
} catch(e) { say("ERROR "+e.toString()); alert("Premiere import failed: "+e.toString()+"\nSee "+cfg.log); }
log.close();
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--export-preset", type=Path, help="Optional Premiere .epr preset; generated JSX will export when explicitly run")
    args = parser.parse_args()
    try:
        xml, jsx = build(args.plan, args.output_dir, args.export_preset)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.exit(2, "Build failed: %s\n" % exc)
    print("Prepared %s\nRun explicitly in Premiere Pro 2024: %s" % (xml, jsx))


if __name__ == "__main__":
    main()
