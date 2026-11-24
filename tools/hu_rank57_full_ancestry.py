"""Read the rendered SB root and exhaustively test rank57's necessary rank conditions; no CFR/registry writes."""
import hashlib, itertools, json, subprocess
from collections import Counter
from pathlib import Path

JS=r'''
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}},c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])vm.runInContext(fs.readFileSync(f,'utf8'),c,{filename:f});
c.__linesQA.render('opfr');const H=[...app.innerHTML.matchAll(/<div class="sec" data-node="[^"]+" id="([^"]+)">/g)];const sec=new Map(H.map((h,i)=>[h[1],app.innerHTML.slice(h.index,H[i+1]?.index??app.innerHTML.length)]));
const root='ln-opfr-f_cbet-milqtu',facing='ln-opfr-f_vs_donk-1wk9say',turn='ln-opfr-t_model-4t8fsk',river='ln-opfr-r_model-8ze7gv';
const n=c.__HU_MODEL_LAST.nodes.find(x=>x.id===river),pn=c.__HU_MODEL_LAST.nodes.find(x=>x.id===turn);assert.equal(n.source,turn);assert.equal(pn.source,facing);assert.equal(n.key,'你過、對手下注、你跟|你下注、對手跟|');assert.deepEqual([n.facts.root.spot,n.facts.root.pot,n.facts.root.stack,n.facts.spr],['SB_BB',6,97,2.733]);
const cells=(id,tx)=>[...sec.get(id).match(new RegExp('<tr[^>]+id="'+id+'-'+tx+'">([\\s\\S]*?)</tr>'))[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
const edge=cell=>{const m=cell.match(/<a class="jmp" href="#([^"]+)">([^<]+)<\/a>/);return m?[m[1],m[2].replace(/≈$/,'')]:[];};
const cls=['TPG','TPW','MID','DRAW','WDRAW'];const routes={};
for(const tx of ['low','mid_high','KQ_high','A_high','paired','mono']){
 const r=cells(root,tx),f=cells(facing,tx),t=cells(turn,tx),v=cells(river,tx);const a={flop:[],turn:[],river:[]};
 for(let i=0;i<5;i++){
  const [to,call]=edge(f[i]),own=edge(r[i]),lead=edge(t[i]);
  if(own[1]==='過' && r[i].includes('class="jmp sub" href="#'+facing+'-'+tx+'"') && to===turn+'-'+tx && call==='跟')a.flop.push(cls[i]);
  if(lead[0]===river+'-'+tx && lead[1]==='下注 ¾')a.turn.push(cls[i]);
  const actual=v[i].split('<small')[0].split('<a class="jmp sub"')[0].replace(/<[^>]*>/g,'').replace(/≈$/,'').trim();if(actual==='下注 ¾')a.river.push(cls[i]);
 }routes[tx]=a;
}console.log(JSON.stringify({start:root,facing,turn,river,routes}));
'''
SIGNATURES={'tools/lines_pipeline/common.py':'7338a5593f19dd878aba5cb21690bc9cf90365b3',
 'tools/lines_pipeline/vclass.py':'512f315c14baa2eb1af908a9f3cbc1f68d57e533',
 'tools/hu_b546_rank70_conditional.py':'8e25e8ae111c2d30c81898a727c71cc0efc752ab'}
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def main():
    for f,h in SIGNATURES.items():assert blob(Path(f).read_bytes())==h
    view=json.loads(subprocess.check_output(['node','-e',JS]));routes=view['routes'];status=json.loads(Path('data/nl2_hu_multiboard_status_current.json').read_bytes())['records']
    m=status[view['river']];assert (m['frequency_rank'],m['label'],m['solver_profile'],m['assumed_model_node_spr'])==(57,'APPROX','SB_BB',2.733)
    assert abs((85/30)/2.733-1)<=.05
    allowed={tx:set(r['flop']) for tx,r in routes.items() if r['flop']}
    assert allowed=={'mid_high':{'TPW','MID','WDRAW'},'KQ_high':{'MID'},'paired':{'TPW','MID'}}
    assert all(r['turn']==r['river']==(['TPG'] if tx=='paired' else []) for tx,r in routes.items())
    R=range(2,15);N=Counter();counterexamples=[];pertexture={tx:Counter() for tx in allowed}
    for f in itertools.combinations_with_replacement(R,3):
        fs=set(f);top=f[-1];tx='paired' if len(fs)<3 else 'A_high' if top==14 else 'KQ_high' if top>=12 else 'mid_high' if top>=10 else 'low'
        if tx not in allowed:continue
        for turn in R:
            board=f+(turn,);bt=max(board)
            if len(set(board))==4:continue # exact paired current texture is necessary; ignoring suits only overestimates.
            for h in itertools.combinations_with_replacement(R,2):
                if max(Counter(board+h).values())>4:continue
                if h[0]==h[1]:
                    cls='S' if h[0] in fs else 'TPG' if h[0]>top else 'MID';turn_top=h[0]>bt
                else:
                    matches=fs.intersection(h)
                    if not matches:cls='WDRAW' # every unpaired missed hand can pass the lone eligible draw bucket in this upper bound.
                    elif len(matches)>1 or f.count(next(iter(matches)))>1:cls='S'
                    else:
                        hit=next(iter(matches));kicker=next(x for x in h if x!=hit)
                        cls='MID' if hit!=top else 'TPG' if kicker>=11 else 'TPW'
                    turn_top=(set(board).intersection(h)=={bt} and board.count(bt)==1 and next((x for x in h if x!=bt),0)>=11)
                # Existing classifier can replace these nominal classes with a straight, flush or better (S),
                # never with an eligible weaker made-hand class. The sets here only enlarge actual possibilities.
                counts={'rank_states':1,'passes_flop_upper_bound':cls in allowed[tx],'passes_turn_upper_bound':turn_top,'passes_both_upper_bounds':bool(cls in allowed[tx] and turn_top)}
                if counts['passes_both_upper_bounds']:counterexamples.append([f,turn,h])
                for k,v in counts.items():N[k]+=v;pertexture[tx][k]+=v
    assert N=={'rank_states':244218,'passes_flop_upper_bound':58327,'passes_turn_upper_bound':12209,'passes_both_upper_bounds':0} and not counterexamples
    parent=status[view['turn']];assert parent['frequency_rank']==9
    print(json.dumps(dict(schema='NL2_R57_RENDERED_ANCESTRY_RANK_UPPER_BOUND_V1',rank=57,model_id=view['river'],
        registry_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),renderer_sha256={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js']},
        classifier_source_git_blobs=SIGNATURES,view=view,profile=dict(spot='SB_BB',actor=0,root=[600,9700],turn=[1200,9400],river=[3000,8500],model_spr=2.733),
        upper_bound_counts=N,by_flop_texture=pertexture,proof_scope='All legal rank multisets, all turn ranks and private ranks. Ignoring suit, opponent blockers, CFR policy and treating any unmatched starting hand as a possible WDRAW can only increase the eligible set.',
        finding='NO_HERO_HOLDING_CAN_PASS_BOTH_RENDERED_STREETS',
        parent_reference_only={'rank':9,'label_at_audit':parent['label'],'original_certified_boards_at_audit':len(parent['certified_3_to_5_exact_flop_boards']),'parent_registry_or_certification_not_modified':True},
        original_flops_repeated=0,new_native_solves=0,new_node_locked_boards=0,new_medium_assessed_boards=0,changed_labels=0),indent=2))
if __name__=='__main__':main()
