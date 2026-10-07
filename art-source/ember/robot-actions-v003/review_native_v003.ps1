param([string]$Workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path)
$ErrorActionPreference = 'Stop'
# 只读 Bitmap 读取及原生整数部件重建比较；不绘制/改写任何 PNG、pose、rig 或 manifest。
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies @('System.Drawing.Common','System.Drawing.Primitives','System.Private.Windows.GdiPlus','System.Private.Windows.Core','System.Runtime','System.Collections') -TypeDefinition @'
using System;
using System.Drawing;
using System.Collections.Generic;
public sealed class RobotNativeReadonlyStats {
    public int Width, Height, Opaque, Components8, MinX=9999, MinY=9999, MaxX=-1, MaxY=-1;
    public bool BinaryAlpha=true;
    public int[] Pixels;
    public string[] RGBColors;
    public static RobotNativeReadonlyStats Read(string path) {
        var r = new RobotNativeReadonlyStats();
        using (var image = new Bitmap(path)) {
            r.Width=image.Width; r.Height=image.Height;
            r.Pixels=new int[r.Width*r.Height];
            var colors=new HashSet<string>();
            for(int y=0;y<r.Height;y++) for(int x=0;x<r.Width;x++) {
                var c=image.GetPixel(x,y); r.Pixels[y*r.Width+x]=c.ToArgb();
                if(c.A!=0 && c.A!=255) r.BinaryAlpha=false;
                if(c.A==0) continue;
                r.Opaque++; r.MinX=Math.Min(r.MinX,x);r.MaxX=Math.Max(r.MaxX,x);
                r.MinY=Math.Min(r.MinY,y);r.MaxY=Math.Max(r.MaxY,y);
                colors.Add(c.R.ToString("X2")+c.G.ToString("X2")+c.B.ToString("X2"));
            }
            r.RGBColors=new string[colors.Count];colors.CopyTo(r.RGBColors);Array.Sort(r.RGBColors);
            var seen=new bool[r.Pixels.Length];var queue=new int[r.Pixels.Length];
            for(int start=0;start<r.Pixels.Length;start++) {
                if(seen[start] || ((uint)r.Pixels[start]>>24)==0) continue;
                r.Components8++;int read=0,write=1;queue[0]=start;seen[start]=true;
                while(read<write) {
                    int p=queue[read++],px=p%r.Width,py=p/r.Width;
                    for(int dy=-1;dy<=1;dy++) for(int dx=-1;dx<=1;dx++) {
                        int nx=px+dx,ny=py+dy;if(nx<0||ny<0||nx>=r.Width||ny>=r.Height) continue;
                        int q=ny*r.Width+nx;if(seen[q] || ((uint)r.Pixels[q]>>24)==0) continue;
                        seen[q]=true;queue[write++]=q;
                    }
                }
            }
        }
        return r;
    }
}
'@
function Get-SourcePath([string]$Path) { Join-Path $Workspace ($Path -replace '^res://','') }
function Get-Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLower() }
$taskManifestPath=Join-Path $PSScriptRoot 'frame_manifest_v003.json'
$taskManifest=Get-Content -LiteralPath $taskManifestPath -Raw|ConvertFrom-Json
$taskManifestSha=Get-Sha $taskManifestPath
$taskErrors=[System.Collections.Generic.List[string]]::new()
$taskRecords=@()
$taskEmissionColors=@('51C5C2','E5A44B','E65B4A')
foreach($taskFrame in $taskManifest.frames|Where-Object{-not $_.reused_original}) {
    $taskPngPath=Get-SourcePath $taskFrame.file
    $taskPosePath=Get-SourcePath $taskFrame.pose_file
    $taskRigPath=Get-SourcePath $taskFrame.source_rig
    $taskIdlePath=Get-SourcePath $taskFrame.source_idle
    $taskPng=[RobotNativeReadonlyStats]::Read($taskPngPath)
    $taskIdle=[RobotNativeReadonlyStats]::Read($taskIdlePath)
    $taskPose=Get-Content -LiteralPath $taskPosePath -Raw|ConvertFrom-Json
    $taskRig=Get-Content -LiteralPath $taskRigPath -Raw|ConvertFrom-Json
    $taskOldRig=Get-Content -LiteralPath (Join-Path $Workspace ('art-source/ember/robot-repair-v002/annotations/rig_'+$taskFrame.direction+'_v002.json')) -Raw|ConvertFrom-Json
    $taskOwnership=@{};$taskParts=@{}
    foreach($taskPart in $taskRig.parts) {
        $taskParts[$taskPart.name]=$taskPart.pixels
        foreach($taskPoint in $taskPart.pixels) {
            $taskIndex=[int]$taskPoint[1]*64+[int]$taskPoint[0]
            if($taskOwnership.ContainsKey($taskIndex)){ $taskErrors.Add('Duplicate ownership '+$taskFrame.id) }
            $taskOwnership[$taskIndex]=$taskPart.name
            if((($taskIdle.Pixels[$taskIndex] -shr 24) -band 255)-ne 255){$taskErrors.Add('Transparent source owned '+$taskFrame.id)}
        }
    }
    if($taskOwnership.Count-ne $taskIdle.Opaque){$taskErrors.Add('Rig coverage differs '+$taskFrame.id)}
    foreach($taskOldPart in $taskOldRig.parts) {
        foreach($taskPoint in $taskOldPart.pixels) {
            $taskIndex=[int]$taskPoint[1]*64+[int]$taskPoint[0]
            $taskNewOwner=$taskOwnership[$taskIndex]
            if($taskOldPart.name-eq 'left_arm') {
                if($taskNewOwner-notin @('left_upper_arm','left_forearm_tool')){$taskErrors.Add('Left-arm source identity changed '+$taskFrame.id)}
            } elseif($taskNewOwner-ne $taskOldPart.name){$taskErrors.Add('Other part identity changed '+$taskFrame.id)}
        }
    }
    # 独立按 pose 声明顺序重建 ARGB 数组，逐点源色，无图像生成写入。
    $taskExpected=[int[]]::new(6144)
    foreach($taskPartName in $taskPose.draw_order) {
        $taskOffset=$taskPose.offsets.$taskPartName
        foreach($taskPoint in $taskParts[$taskPartName]) {
            $taskTargetX=[int]$taskPoint[0]+[int]$taskOffset[0]
            $taskTargetY=[int]$taskPoint[1]+[int]$taskOffset[1]
            if($taskTargetX-lt 0-or $taskTargetY-lt 0-or $taskTargetX-ge 64-or $taskTargetY-ge 96){$taskErrors.Add('Part overflow '+$taskFrame.id);continue}
            $taskExpected[$taskTargetY*64+$taskTargetX]=$taskIdle.Pixels[[int]$taskPoint[1]*64+[int]$taskPoint[0]]
        }
    }
    foreach($taskPatch in $taskPose.joint_pixels) {
        if([string]::IsNullOrWhiteSpace($taskPatch.anatomical_reason)){$taskErrors.Add('Unexplained joint pixel '+$taskFrame.id)}
        $taskSourceIndex=[int]$taskPatch.source_rgba_at[1]*64+[int]$taskPatch.source_rgba_at[0]
        $taskExpected[[int]$taskPatch.at[1]*64+[int]$taskPatch.at[0]]=$taskIdle.Pixels[$taskSourceIndex]
    }
    $taskDifferences=0;$taskIdleDifferences=0;$taskFootDifferences=0
    for($taskIndex=0;$taskIndex-lt 6144;$taskIndex++) {
        if($taskExpected[$taskIndex]-ne $taskPng.Pixels[$taskIndex]){$taskDifferences++}
        if($taskIdle.Pixels[$taskIndex]-ne $taskPng.Pixels[$taskIndex]){$taskIdleDifferences++}
        if($taskIndex-ge 74*64-and $taskIndex-lt 80*64-and $taskIdle.Pixels[$taskIndex]-ne $taskPng.Pixels[$taskIndex]){$taskFootDifferences++}
    }
    $taskHeadDifferences=0;$taskHeadOffset=$taskPose.offsets.head
    foreach($taskPoint in $taskParts.head) {
        $taskExpectedHead=$taskIdle.Pixels[[int]$taskPoint[1]*64+[int]$taskPoint[0]]
        $taskActualHead=$taskPng.Pixels[([int]$taskPoint[1]+[int]$taskHeadOffset[1])*64+[int]$taskPoint[0]+[int]$taskHeadOffset[0]]
        if($taskExpectedHead-ne $taskActualHead){$taskHeadDifferences++}
    }
    $taskShoulderAnchored=($taskPose.offsets.left_upper_arm[0]-eq $taskPose.offsets.torso[0]-and $taskPose.offsets.left_upper_arm[1]-eq $taskPose.offsets.torso[1])
    $taskPaletteExtraneous=@($taskPng.RGBColors|Where-Object{$_-notin $taskIdle.RGBColors})
    $taskEmissionFound=@($taskPng.RGBColors|Where-Object{$_-in $taskEmissionColors})
    $taskToolOwned=$true;$taskToolVisible=0;$taskToolCount=0
    $taskToolOffset=$taskPose.offsets.left_forearm_tool
    $taskOldLeft=$taskOldRig.parts|Where-Object name -eq 'left_arm'
    foreach($taskPoint in $taskOldLeft.pixels) {
        $taskSourceIndex=[int]$taskPoint[1]*64+[int]$taskPoint[0]
        $taskArgb=$taskIdle.Pixels[$taskSourceIndex]
        $taskRgb=('{0:X6}'-f ([int64]$taskArgb-band 0xFFFFFF))
        if($taskRgb-notin @('7B4D35','B77C4B','E2B77A')){continue}
        $taskToolCount++
        if($taskOwnership[$taskSourceIndex]-ne 'left_forearm_tool'){$taskToolOwned=$false}
        $taskTargetIndex=([int]$taskPoint[1]+[int]$taskToolOffset[1])*64+[int]$taskPoint[0]+[int]$taskToolOffset[0]
        if($taskPng.Pixels[$taskTargetIndex]-eq $taskArgb){$taskToolVisible++}
    }
    if($taskDifferences-ne 0-or $taskFootDifferences-ne 0-or $taskHeadDifferences-ne 0-or -not $taskShoulderAnchored-or -not $taskToolOwned-or $taskToolCount-ne $taskToolVisible-or $taskPng.Components8-ne 1-or -not $taskPng.BinaryAlpha-or $taskPaletteExtraneous.Count-ne 0-or $taskEmissionFound.Count-ne 0){$taskErrors.Add('Native frame check failed '+$taskFrame.id)}
    if($taskPng.Width-ne 64-or $taskPng.Height-ne 96-or $taskPng.MaxX-$taskPng.MinX+1-gt 40-or $taskPng.MaxY-$taskPng.MinY+1-gt 64-or $taskPng.MaxY-ne 79){$taskErrors.Add('Frame dimensions/bbox/foot failed '+$taskFrame.id)}
    if((Get-Sha $taskPngPath)-ne $taskFrame.sha256-or (Get-Sha $taskPosePath)-ne $taskFrame.pose_sha256-or (Get-Sha $taskRigPath)-ne $taskFrame.source_rig_sha256){$taskErrors.Add('Manifest SHA binding failed '+$taskFrame.id)}
    $taskRecords += [ordered]@{id=$taskFrame.id;file=$taskFrame.file;sha256=(Get-Sha $taskPngPath);pose_file=$taskFrame.pose_file;pose_sha256=(Get-Sha $taskPosePath);rig_file=$taskFrame.source_rig;rig_sha256=(Get-Sha $taskRigPath);independent_reconstructed_rgba_differences=$taskDifferences;changed_pixels_vs_idle=$taskIdleDifferences;head_translated_rgba_differences=$taskHeadDifferences;feet_rows_74_79_differences=$taskFootDifferences;shoulder_anchored_to_torso=$taskShoulderAnchored;tool_original_hand='left';tool_source_pixel_count=$taskToolCount;tool_original_points_visible_unchanged=$taskToolVisible;tool_source_ownership_valid=$taskToolOwned;components8=$taskPng.Components8;binary_alpha=$taskPng.BinaryAlpha;palette_rgb=$taskPng.RGBColors;off_source_palette_colors=$taskPaletteExtraneous;runtime_emission_colors_found=$taskEmissionFound;joint_pixel_annotation_count=$taskPose.joint_pixels.Count}
}
if($taskRecords.Count-ne 20-or $taskManifest.status-ne 'PASS'){ $taskErrors.Add('Expected final PASS manifest with 20 new PNG') }
$taskFrozen=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'native_frozen_before_metadata_fix_v003.json') -Raw|ConvertFrom-Json
foreach($taskRecord in $taskFrozen){if((Get-Sha $taskRecord.file)-ne $taskRecord.sha256){$taskErrors.Add('Frozen source changed '+$taskRecord.file)}}
if((Get-Sha $taskManifestPath)-ne $taskManifestSha){$taskErrors.Add('Manifest changed during independent review')}
$taskReview=[ordered]@{schema_version=1;status=$(if($taskErrors.Count-eq 0){'PASS'}else{'FAIL'});errors=@($taskErrors.ToArray());date='2026-10-06';reviewer='/root/robot_frame_audit';source_manifest_sha256=$taskManifestSha;source_manifest='art-source/ember/robot-actions-v003/frame_manifest_v003.json';new_png_count=20;frozen_input_count=$taskFrozen.Count;frozen_inputs_unchanged=($taskErrors.Count-eq 0);visual_review_author='/root';visual_review='Root viewed the second 4x board and accepted shoulder stability, retained proportions and no new visible fragments.';viewed_contact_sheet='art-source/ember/robot-actions-v003/new_actions_contact_4x_v003.png';viewed_contact_sheet_sha256=(Get-Sha (Join-Path $PSScriptRoot 'new_actions_contact_4x_v003.png'));tool_identity_basis='Original left_arm ownership from v002 rig. Bronze accents on head/torso/empty wrist are not tool pixels.';image_editing='NONE: readonly System.Drawing Bitmap decode and integer ARGB reconstruction compare; no PNG write.';frames=$taskRecords}
$taskReview|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'native_review_v003.json') -Encoding utf8
Write-Output ('NATIVE_REVIEW '+$taskReview.status+' frames='+$taskRecords.Count+' errors='+$taskErrors.Count+' manifest='+$taskManifestSha)
if($taskErrors.Count-ne 0){Write-Output $taskErrors;exit 1}
