import unittest
from harness import Harness,r
from lupa.lua54 import LuaError
import test_projectiles as projectile_tests


class DecorationTests(unittest.TestCase):
    def test_native_signature_with_signed_framework_reads(self):
        for extreme in [False, True]:
            h = Harness(extreme)
            h.lua.globals().core.readInteger = lambda a: int.from_bytes(h.uc.mem_read(a, 4), 'little', signed=True)
            h.lua.globals().core.readSmallInteger = lambda a: int.from_bytes(h.uc.mem_read(a, 2), 'little', signed=True)
            resolved = h.lua.execute(b"return require('decorations')").resolve(h.scan)
            self.assertEqual(resolved[b'queue'], 0x489100 + (0x110 if extreme else 0))
            # Preserve the guard: a genuinely changed instruction must fail.
            h.put(resolved[b'queue'], 0x90, 1)
            with self.assertRaises(LuaError):
                h.lua.execute(b"return require('decorations')").resolve(h.scan)

    def test_native_menu_group_pagination_selection_and_reopening(self):
        h=Harness()
        h.lua.globals().core.AOBScan=h.scan
        h.lua.execute(b'''
            callbacks={};handlers={};sent={};drawn={};closed=0;consumed=0
            registerObject=function(v) return v end
            ffi={cast=function(kind,v)
                if kind=='void (__thiscall *)(void *)' then
                    reset_input_address=v
                    return function(mouse) assert(mouse==123);consumed=consumed+1 end
                end
                if type(v)=='function' then callbacks[#callbacks+1]=v;return #callbacks end
                return v end,new=function(kind,values) return values end}
            remote={interface={core=core,manager={getAvailableMenuID=function(n) return n end,
                getAvailableModalMenuID=function(n) return n end}},events={
                receive=function(key,handler) handlers[key]=handler end,
                send=function(key,value) assert(consumed==closed);sent[#sent+1]=value end}}
            api={ui={Menu={createMenu=function(self,spec) menu_spec=spec;return spec end},
                ModalMenu={createModalMenu=function(self,spec) return spec end}}}
            game={Input={mouseState=123},UI={activateModalMenu=function() closed=closed+1 end},Rendering={
                ButtonState={x=0,y=0},pDrawBufferChoiceValue={[0]=1},
                drawBlendedBlackBox=function() end,
                renderTextToScreenConst=function(self,label) drawn[#drawn+1]=label end}}
        ''')
        from harness import ROOT
        # The UI's LuaJIT environment exposes core only through remote.interface.
        h.lua.execute(b'core=nil')
        h.lua.execute((ROOT/'ui/decorations.lua').read_bytes())
        h.lua.execute(b'''
            assert(menu_spec.menuItems[1].menuItemType==0x01000000)
            assert(menu_spec.menuItems[13].menuItemType==0x66)
            local choices={};for n=1,33 do choices[n]={id=n,label='Variant '..n} end
            local open=handlers['custom-projectiles/decorations/open']
            open(nil,{language='german',choices=choices})
            local click,render=callbacks[1],callbacks[2]
            render(1);assert(drawn[1]=='Feuerkorb')
            assert(game.Rendering.pDrawBufferChoiceValue[0]==1)
            for n=1,10 do click(102) end -- clamp to last page (32,33)
            click(2);assert(sent[1].id==33 and closed==1)
            click(8);assert(#sent==1) -- empty row cannot select another variant
            for n=1,10 do click(101) end
            click(1);assert(sent[2].id==0)
            click(102);open(nil,{language='english',choices=choices})
            click(2);assert(sent[3].id==1) -- reopening resets pagination
            click(103);assert(closed==4 and consumed==4)
        ''')
        # The real native reset consumes this frame's button edges and held
        # state without moving the pointer. Repeat against both executables.
        pattern=h.scans[-1]
        for extreme in [False,True]:
            native=Harness(extreme);address=native.scan(pattern)
            mouse=native.allocate(0x274)
            for offset in range(0x28,0x58,4):native.put(mouse+offset,1)
            native.put(mouse+0x10,512);native.put(mouse+0x14,256)
            native.call(address,registers={r.UC_X86_REG_ECX:mouse})
            self.assertTrue(all(native.get(mouse+o)==0 for o in range(0x28,0x58,4)))
            self.assertEqual((native.get(mouse+0x10),native.get(mouse+0x14)),(512,256))

    def prepare_module(self, config, extreme=False):
        h=Harness(extreme)
        h.hooks=[];h.actions=[];h.protocols=[];h.opened=[];h.selected=[]
        def hook(callback,address,count,abi,size):
            h.hooks.append((callback,address,count,abi,size))
            return lambda *args:h.actions.append((address,args)) or 0
        def expose(address,count,abi):
            if abi==1:
                return lambda this,*args:h.call(address,args,{r.UC_X86_REG_ECX:this})
            return lambda *args:h.call(address,args)
        h.lua.globals().core.hookCode=hook
        h.lua.globals().core.exposeCode=expose
        h.lua.globals().register_protocol=lambda handler:h.protocols.append(handler) or 7
        h.lua.globals().invoke_protocol=lambda number,context:h.selected.append((number,context))
        h.lua.globals().open_menu=lambda:h.opened.append(True)
        h.lua.execute(b'''modules.protocol={
            registerCustomProtocol=function(self,extension,name,mode,length,handler)
                assert(mode=='LOCKSTEP' and length==12);return register_protocol(handler) end,
            invokeProtocol=function(self,...) return invoke_protocol(...) end}
            package.loaded.decoration_ui={prepare=function()
                return open_menu,function(callback) choose_decoration=callback end end}''')
        h.native_decor=h.lua.execute(b"return (require('decorations'))").resolve(h.scan)
        h.module.apply(h.config(config))
        h.v={k:v for _,_,values in h.blobs.values() for k,v in values.items()}
        for owner in range(9):h.put(h.v['TEAMTBL']+owner*4,owner)
        return h

    def test_integrated_profile_fire_fortification_and_saved_continuation(self):
        for extreme in [False,True]:
            config={'decorations':{'frost':{}},'units':{'Catapult':{'count':2,
                'on_fortification':{'count':3},'near_decorations':[
                    {'decoration':'frost','projectile':'mangonel_pebble'}]}}}
            h=self.prepare_module(config,extreme);u=h.unit(1,39)
            e=h.v['ENTITYARRAY']+232
            for off,value in [(0x28,2),(0x2a,14),(0x44,40),(0x46,40)]:h.put(e+off,value,2)
            h.put(e+0x30,77);h.put(h.v['DECORVARIANT']+4,1);h.put(h.v['DECORUID']+4,77)
            h.call(h.v['REBUILDDECOR'])
            self.assertEqual(h.call(h.v['PROFILE'],[1]),160)
            shots=projectile_tests.NativeTests().fire(h,1)
            self.assertEqual(len(shots),2);self.assertTrue(all(s[9]==4 for s in shots))
            h.put(h.v['TILEROWS']+40*12,16000);h.put(h.v['TILEFLAGS']+16040*4,0x100)
            h.put(u+0xbc,20,2)
            self.assertEqual(h.call(h.v['PROFILE'],[1]),161)
            h.put(h.v['NATIVESEENT']+4,0)
            self.assertEqual(len(projectile_tests.NativeTests().fire(h,1)),3)
            state=h.sections[b'projectileModifier'];saved=projectile_tests.NativeTests().state_handle(h)
            state.serialize(state,saved)
            h.put(h.v['DECORVARIANT']+4,0);h.call(h.v['REBUILDDECOR'])
            self.assertEqual(h.call(h.v['PROFILE'],[1]),119)
            state.deserialize(state,saved)
            self.assertEqual(h.call(h.v['PROFILE'],[1]),161)
            h.put(e+0x28,0,2);h.call(h.v['REBUILDDECOR'])
            self.assertEqual(h.call(h.v['PROFILE'],[1]),119)

    def test_decorations_without_unit_rules_still_install_and_select_native_build_mode(self):
        h=self.prepare_module({'decorations':{'frost':{}}})
        self.assertEqual(len(h.hooks),2)
        action,address,count,abi,size=h.hooks[1]
        action(148);self.assertEqual(h.opened,[True]);self.assertEqual(h.actions,[])
        h.lua.globals().choose_decoration(1)
        self.assertEqual(h.actions,[(address,(148,))])
        queue=h.hooks[0][0]
        native=h.native_decor
        h.put(native[b'x'],17);h.put(native[b'y'],29);h.put(native[b'kind'],14)
        queue(123,69)
        self.assertEqual(h.selected[0][0],7)
        self.assertEqual(h.selected[0][1][b'decoration'],1)
        action(100) # choosing another building clears the custom selection
        queue(123,69)
        self.assertEqual(len(h.selected),1)
        self.assertEqual(h.actions[-1],(h.hooks[0][1],(123,69)))

    def test_sparse_rules_validate_all_fields_and_enable_native_cadence(self):
        h=Harness();cfg=h.lua.execute(b"return (require('configuration'))")
        source={'decorations':{'frost':{}},'units':{'Arabian horse archer':{
            'near_decorations':[{'decoration':'frost','interval_standing':300}]}}}
        normalized=cfg.validate(h.config(source))
        rules=normalized[b'units'][b'Arabian horse archer'][b'near_decorations']
        self.assertEqual(rules[1][b'ground'][b'interval_standing'],300)
        self.assertEqual(rules[1][b'ground'][b'interval_moving'],0)
        self.assertTrue(h.lua.execute(b"return (require('cadence'))").required(normalized))
        for field,value in [('typo',1),('count',65),('projectile','undefined'),
                            ('near_decorations',[]),('on_fortification',{})]:
            source['units']['Arabian horse archer']['near_decorations'][0][field]=value
            with self.assertRaises(LuaError):cfg.validate(h.config(source))
            del source['units']['Arabian horse archer']['near_decorations'][0][field]
    def test_native_signatures_are_unique_both_executables(self):
        for extreme in [False,True]:
            h=Harness(extreme)
            def locate(pattern):
                address=h.scan(pattern)
                with self.assertRaises(RuntimeError):h.scan(pattern,address+1)
                return address
            m=h.lua.execute(b"return (require('decorations'))")
            resolved=m.resolve(locate)
            self.assertEqual(resolved[b'queue'],0x489100+(0x110 if extreme else 0))
            self.assertEqual(resolved[b'commandID'],69)

    def test_lockstep_payload_is_independent_of_receiver_selection(self):
        h=Harness();m=h.lua.execute(b"return (require('decorations'))")
        definitions=m.definitions(h.config({'frost':{'label':'Frost brazier'}}))
        by_id=h.lua.table_from({1:definitions[b'frost']})
        calls=[];sender=[2]
        protocol=m.protocol(by_id,lambda:sender[0],lambda *args:calls.append(args))
        meta=h.lua.execute(b'''local values={}; return {values=values,parameters={
            serializeInteger=function(self,v) values[#values+1]=v end,
            deserializeInteger=function(self) return table.remove(values,1) end}}''')
        context=h.config({'x':17,'y':29,'decoration':1})
        protocol.schedule(protocol,meta,context)
        self.assertEqual(list(meta[b'values'].values()),[17,29,1])
        protocol.execute(protocol,meta)
        self.assertEqual(calls,[(2,17,29,1)])
        for context in [{'x':3200,'y':0,'decoration':1},{'x':0,'y':-1,'decoration':1},
                        {'x':0,'y':0,'decoration':2}]:
            self.assertFalse(m.valid_placement(h.config(context),by_id))
            with self.assertRaises(LuaError):protocol.schedule(protocol,meta,h.config(context))

    def test_actual_native_construction_cost_ownership_and_removal(self):
        for extreme in [False,True]:
            h=self.prepare_module({'decorations':{'frost':{}}},extreme);n=h.native_decor
            tile=40*400+40;tilemap=h.v['TILEFLAGS']-0x165160
            for y in range(400):h.put(h.v['TILEROWS']+y*12,y*400)
            h.put(h.v['TILEFLAGS']+tile*4,0x100)
            h.put(tilemap+0x29fa30+tile,45,1)
            h.put(h.get(n[b'valid']+8)+tile*2,1,2)
            body=bytes(h.uc.mem_read(h.spawner,0x500));offset=body.index(b'\x80\xbc\x01')
            h.put(h.get(h.spawner+offset+3)+tile,1,1)
            state=n[b'entityState'];h.put(state+8,25)
            h.put(n[b'invoker'],1);h.put(n[b'gameMode'],6)
            gold=n[b'gold']+0x39f4;h.put(gold,1000)
            protocol=h.protocols[0]
            def place():
                meta=h.lua.execute(b'''local values={};return {parameters={
                    serializeInteger=function(self,v) values[#values+1]=v end,
                    deserializeInteger=function(self) return table.remove(values,1) end}}''')
                protocol.schedule(protocol,meta,h.config({'x':320,'y':320,'decoration':1}))
                protocol.execute(protocol,meta)
            entity=h.v['ENTITYARRAY']+25*232
            # Native cursor validation rejects another player's wall.
            h.put(tilemap+0x2c6e50+tile,1,1);place()
            self.assertEqual(h.get(entity+0x28,2),0);self.assertEqual(h.get(gold),1000)
            h.put(tilemap+0x2c6e50+tile,0,1);h.put(gold,4);place()
            self.assertEqual(h.get(entity+0x28,2),0);self.assertEqual(h.get(gold),4)
            h.put(gold,1000);place()
            self.assertEqual([h.get(entity+o,2) for o in [6,0x28,0x2a,0x2c,0x3c,0x44,0x46]],
                             [138,1,14,1,45,40,40])
            self.assertEqual(h.get(gold),995)
            self.assertEqual(h.get(h.v['DECORVARIANT']+100),1)
            self.assertEqual(h.get(h.v['DECORUID']+100),h.get(entity+0x30))
            # The real native proximity predicate sees ordinary braziers but
            # skips this custom variant, including after its newborn update.
            update=h.blobs['spriteUpdateOriginal'][2]['ENTITYRESUME']-6
            h.call(update,registers={r.UC_X86_REG_ECX:state})
            near=n[b'filter']-0x27
            self.assertEqual(h.call(near,[40,40,45],{r.UC_X86_REG_ECX:state}),0)
            h.put(h.v['DECORVARIANT']+100,0)
            self.assertEqual(h.call(near,[40,40,45],{r.UC_X86_REG_ECX:state}),1)
            h.put(h.v['DECORVARIANT']+100,1)
            # Native deletion at a tile, also called by the area-removal command.
            remove=h.scan(b'57 8B 7C 24 08 66 F7 04 7D ? ? ? ? 00 10 74 63')
            h.call(remove,[tile],{r.UC_X86_REG_ECX:state})
            self.assertNotIn(h.get(entity+0x28,2),[1,2])
            h.call(h.v['REBUILDDECOR'])
            self.assertEqual(h.get(h.v['DECORVARIANT']+100),0)

    def prepare_grid(self,extreme=False):
        h=Harness(extreme)
        runtime=h.lua.execute(b"return (require('decoration_runtime'))")
        values={'MAXTYPES':80,'UNITARRAY':h.base,'ENTITYARRAY':0x3000014}
        for name,size in [('DECORVARIANT',12000),('DECORUID',12000),('DECORNEXT',12000),
                          ('DECORGM',136),('DECORGRID',40000),('DECORRULEMAP',80*408),('DECORRULEST',320)]:
            values[name]=h.allocate(size)
        rebuild=h.assemble(runtime.rebuild,h.config(values));query=h.assemble(runtime.profile,h.config(values))
        unit=h.unit(1,22)
        h.put(values['DECORRULEST']+22*4,1)
        rule=values['DECORRULEMAP']+22*408+12
        h.put(rule,1);h.put(rule+4,160);h.put(rule+8,161)
        entity=values['ENTITYARRAY']+232
        for off,value in [(0x28,2),(0x2a,14),(0x44,40),(0x46,40)]:h.put(entity+off,value,2)
        h.put(entity+0x30,777);h.put(values['DECORVARIANT']+4,1);h.put(values['DECORUID']+4,777)
        return h,values,unit,entity,rebuild,query

    def test_grid_matches_native_square_and_height_boundaries(self):
        for extreme in [False,True]:
            h,v,u,e,rebuild,query=self.prepare_grid(extreme)
            for dx in range(-5,6):
                for dy in range(-5,6):
                    h.put(e+0x44,40+dx,2);h.put(e+0x46,40+dy,2)
                    h.call(rebuild)
                    self.assertEqual(h.call(query,[1,22]),160 if abs(dx)<=3 and abs(dy)<=3 else 22)
            h.put(e+0x44,40,2);h.put(e+0x46,40,2)
            for height in [0,44,45,46,100]:
                h.put(e+0x3c,height,2);h.call(rebuild)
                self.assertEqual(h.call(query,[1,102]),161 if height<45 else 102)
            # Crossing a map edge cannot index before/after the grid allocation.
            for position in [0,399]:
                h.put(u+0xc4,position,2);h.put(u+0xc6,position,2)
                h.put(e+0x44,position,2);h.put(e+0x46,position,2);h.put(e+0x3c,0,2)
                h.call(rebuild);self.assertEqual(h.call(query,[1,22]),160)
            h.put(e+0x30,778);h.call(rebuild)
            self.assertEqual(h.call(query,[1,22]),22)

    def test_first_configured_rule_wins_and_dead_entities_do_not_trigger(self):
        h,v,u,e,rebuild,query=self.prepare_grid()
        rule=v['DECORRULEMAP']+22*408+24
        h.put(rule,2);h.put(rule+4,162);h.put(rule+8,163)
        other=e+232;h.uc.mem_write(other,bytes(h.uc.mem_read(e,232)))
        h.put(other+0x30,778);h.put(v['DECORVARIANT']+8,2);h.put(v['DECORUID']+8,778)
        h.call(rebuild);self.assertEqual(h.call(query,[1,22]),160)
        h.put(e+0x28,0,2);h.call(rebuild)
        self.assertEqual(h.call(query,[1,22]),162)
        h.put(other+0x28,0,2);h.call(rebuild)
        self.assertEqual(h.call(query,[1,22]),22)
