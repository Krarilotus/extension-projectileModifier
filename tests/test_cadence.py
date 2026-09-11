"""Actual artillery animation/ammunition paths, isolated and integrated."""
import unittest
import re
from harness import r
import test_projectiles as projectile_tests


class CadenceTests(unittest.TestCase):
    def test_trebuchet_rest_resolution_rejects_conflicting_native_data(self):
        from harness import Harness
        for extreme in [False,True]:
            for changed in ['pose','branch']:
                with self.subTest(extreme=extreme,changed=changed):
                    h=Harness(extreme)
                    if changed=='pose':
                        site=h.scan(b'69 DB 90 04 00 00 8B 83 ? ? ? ? 0F BE 80 ? ? ? ? 3B C2 89 83 ? ? ? ? 7F 1A 5F 5E')
                        h.put(h.get(site+0x68)+35,26,1)
                        message='unsupported trebuchet loaded pose'
                    else:
                        site=h.scan(b'B9 ? ? ? ? 66 3B C1 0F 85 ? ? ? ? C7 86 ? ? ? ? 05 00 00 00 89 96 ? ? ? ? 66 89 96 ? ? ? ?')
                        h.put(site+10,0x70000000)
                        message='unsupported trebuchet firing speed'
                    with self.assertRaisesRegex(Exception,message):
                        h.enable({'Trebuchet':{'interval':400}})
                    self.assertEqual(h.writes,[],'reject before installing hooks')

    def test_trebuchet_cooldown_waits_loaded_then_runs_the_entire_swing(self):
        for extreme in [False, True]:
            with self.subTest(extreme=extreme):
                h,a,tick=self.integrated('Trebuchet',40,0x569410,{'interval':400},extreme)
                events=[]; swings=[]; current=[]; resting=[]
                for t in range(1100):
                    queued,shots=tick()
                    self.assertFalse(queued)
                    if shots: events.append(t)
                    state=h.get(a+0x2c0,2)
                    cycle=h.get(a+0x2b0)
                    if state==4:
                        current.append((cycle,h.get(a+0x74),bool(shots)))
                    elif current:
                        swings.append(current);current=[]
                    if events and state==2 and cycle==35:
                        resting.append(t)
                        # Facing zero renders the loaded body pose 23, not
                        # firing pose 26 (the previous mid-swing hold point).
                        self.assertEqual(h.get(a+0x74),(23-1)*8+5)
                self.assertEqual(events,[219,619,1019])
                self.assertEqual(len(swings),3)
                self.assertEqual(swings[0],swings[1])
                self.assertEqual(swings[0],swings[2])
                self.assertGreater(len(resting),200)
                self.assertEqual(h.get(a+0x362,2),997)

    def test_trebuchet_loaded_gate_preserves_cows_and_late_release_checks(self):
        for extreme in [False,True]:
            setup=self.prepare('Trebuchet',40,27,0x569410,extreme)
            _,h,v,*_=setup
            a=h.unit(1,40)
            for off,value,size in [(0x2c0,2,2),(0x2b0,35,4),(0x40,5,4),(0x44,5,4)]:
                h.put(a+off,value,size)
            def hold(remaining,blocked=0):
                return h.call(v['SHOULDHOLD'],[1,v['RELEASECYCLE'],remaining,blocked])
            self.assertEqual(hold(10),1)
            self.assertEqual(hold(9),0)
            self.assertEqual(hold(9,1),1)
            h.put(a+0x3b0,1,2)
            self.assertEqual(hold(400,1),0)
            h.put(a+0x3b0,0,2);h.put(a+0x2b0,34)
            self.assertEqual(hold(400,1),0)
            h.put(a+0x2c0,4,2);h.put(a+0x2b0,1)
            self.assertEqual(hold(3),0)
            h.put(a+0x2b0,2)
            self.assertEqual(hold(0),0)
            self.assertEqual(hold(0,1),1)

    def test_trebuchet_loaded_wait_survives_save_load_and_crew_loss(self):
        observer=projectile_tests.NativeTests()
        h,a,tick=self.integrated('Trebuchet',40,0x569410,{'interval':400})
        for _ in range(530):tick()
        self.assertEqual((h.get(a+0x2c0,2),h.get(a+0x2b0)),(2,35))
        handle=observer.state_handle(h);state=h.sections[b'projectileModifier']
        state.serialize(state,handle)
        native=bytes(h.uc.mem_read(a,0x490))
        first=[tick() for _ in range(105)]
        h.uc.mem_write(a,native)
        state.deserialize(state,handle)
        self.assertEqual(first,[tick() for _ in range(105)])
        self.assertTrue(any(shots for _,shots in first))
        # After another reload, missing crew holds the same loaded pose even
        # when the interval expires. Re-boarding permits the full swing.
        for _ in range(300):tick()
        h.put(a+0x3b4,0,2)
        for _ in range(130):self.assertEqual(tick(),([],[]))
        self.assertEqual((h.get(a+0x2c0,2),h.get(a+0x2b0)),(2,35))
        h.put(a+0x3b4,3,2)
        shots=[i for i in range(15) if tick()[1]]
        self.assertEqual(shots,[9])

    def test_animation_hook_is_installed_only_when_needed(self):
        observer=projectile_tests.NativeTests()
        for settings in [{'count':3},{'interval':100,'sync_to_animation':False}]:
            h=observer.prepare({'Catapult':settings})
            self.assertNotIn('configuredAnimationHold',h.blobs)
            self.assertFalse(any(p.startswith(b'A1 ? ? ? ? 69 C0') for p in h.scans))
        h=observer.prepare({'Catapult':{'on_fortification':{'interval':100}}})
        self.assertIn('configuredAnimationHold',h.blobs)

    def test_unconfigured_infantry_animation_changes_do_not_block_siege(self):
        from harness import Harness
        for extreme in [False,True]:
            h=Harness(extreme)
            at=h.scan(b'0F BE 82 ? ? ? ? 85 C0 89 86 ? ? ? ? 7E 6D 0F BF 96 ? ? ? ? 8D 84 C2 79 01 00 00')
            h.put(at,0x90,1)  # simulate an unrelated module changing archers
            h.enable({'Catapult':{'interval':300}})
            self.assertIn('configuredAnimationHold',h.blobs)

    def test_native_cooldown_continues_during_a_crew_hold(self):
        h,a,tick=self.integrated('Catapult',39,0x568320,{'interval':250})
        events=[]
        for t in range(470):
            if t==150: h.put(a+0x3b4,0,2)
            if t==420: h.put(a+0x3b4,2,2)
            queued,shots=tick()
            self.assertFalse(queued)
            if shots: events.append(t)
        self.assertEqual(events,[99,420])

    def test_native_crew_defaults_and_explicit_overrides(self):
        observer=projectile_tests.NativeTests()
        for name,kind,crew in [('Catapult',39,2),('Trebuchet',40,3),('Mangonel',41,2),
                               ('Tower ballista',61,2),('Fire ballista',77,2)]:
            with self.subTest(unit=name):
                h=observer.prepare({name:{'interval':250}})
                a=h.unit(1,kind);h.unit(2,22,owner=2,x=44)
                self.assertEqual(h.get(h.v['MANNEDT']+kind*4),crew)
                h.put(a+0x3b4,crew-1,2)
                self.assertEqual(observer.tick(h,1),[])
                self.assertEqual(h.get(a+0x2c0,2),0)
                h.put(a+0x3b4,crew,2)
                self.assertEqual(observer.tick(h,1),[])
                self.assertEqual(h.get(a+0x2c0,2),2)
        for extra in [{'require_manned':False},{'sync_to_animation':False}]:
            h=observer.prepare({'Catapult':dict(interval=250,**extra)})
            a=h.unit(1,39);h.unit(2,22,owner=2,x=44)
            self.assertEqual(h.get(h.v['MANNEDT']+39*4),0)
            shots=observer.tick(h,1)
            if 'sync_to_animation' in extra: self.assertEqual(len(shots),1)
            else: self.assertEqual(h.get(a+0x2c0,2),2)

    def test_next_reload_prepares_during_a_long_staggered_volley(self):
        h,a,tick=self.integrated('Catapult',39,0x568320,
            {'interval':250,'count':64,'stagger_min':3,'stagger_max':3})
        releases=[];queued=[]
        for t in range(450):
            following,first=tick()
            if following: queued.append(t)
            if first: releases.append(t)
        self.assertEqual(releases,[99,349])
        self.assertEqual(queued[:63],list(range(102,289,3)))
        self.assertEqual(h.get(a+0x362,2),998)

    def prepare(self, name, kind, frame, handler, extreme):
        observer=projectile_tests.NativeTests()
        h=observer.prepare({name:{'count':1,'inaccuracy':0}},extreme)
        lib=h.lua.execute(b"return (require('cadence'))")
        animation=h.scan(b'A1 ? ? ? ? 69 C0 90 04 00 00 01 9C 30 54 06 00 00')
        end=animation+0xa1
        self.assertEqual(h.get(end,1),0x69)
        handler += h.v['FIREPROJ']-0x532700
        release=lib.resolve(h.scan)[kind]
        self.assertGreater(release,0)
        rest=lib.resolve_trebuchet_rest(h.scan,release if kind==40 else None)
        values=dict(h.v, RELEASECYCLE=release, ANIMATIONDONE=end,
                    TREBRESTCYCLE=rest[b'cycle'] if rest else -1,
                    TREBRELEASELEAD=rest[b'lead'] if rest else 0,
                    RESUME=animation+18, BLOCKEDT=h.allocate(h.v['MAXUNITS']*4))
        def assemble(code):
            used={k:v for k,v in values.items() if re.search(rb'\b'+k.encode()+rb'\b',code)}
            return h.assemble(code,h.config(used))
        values['SHOULDHOLD']=assemble(lib.hold_code)
        hook=assemble(lib.animation_hook)
        import struct
        h.uc.mem_write(animation+11,b'\xe9'+struct.pack('<i',hook-(animation+16))+b'\x90\x90')
        return observer,h,values,animation,end,handler

    def simulate(self, setup, kind, period, duration=600):
        observer,h,v,animation,end,handler=setup
        a=h.unit(1,kind)
        h.put(h.v['CURUNIT'],1)
        h.put(v['COOLDOWNT']+4,0)
        h.put(v['BLOCKEDT']+4,0)
        for off,value,size in [(0x2c0,2,2),(0x3b4,2,2),(0x362,1000,2),
                              (0xbe,352,2),(0xc0,320,2),(0x39c,5,2),(0x344,0xffff,2)]:
            h.put(a+off,value,size)
        events=[]
        # Sound's device side effects are unrelated to animation/ammunition.
        sound=0x449dc0+(0x2e0 if h.v['FIREPROJ']!=0x532700 else 0)
        def no_sound(h):
            esp=h.uc.reg_read(r.UC_X86_REG_ESP)
            h.uc.reg_write(r.UC_X86_REG_EIP,h.get(esp))
            h.uc.reg_write(r.UC_X86_REG_ESP,esp+16)
        for tick in range(duration):
            h.put(v['COOLDOWNT']+4,max(0,h.get(v['COOLDOWNT']+4)-1))
            h.put(v['NATIVESEENT']+4,0)
            h.call(animation,registers={r.UC_X86_REG_ESI:v['UNITSTATE'],r.UC_X86_REG_EBX:1,
                                        r.UC_X86_REG_EBP:0},stop=end)
            shots=[]
            h.call(handler,callbacks={h.spawner:observer.spawn_callback(shots),sound:no_sound})
            if shots:
                self.assertEqual(h.get(a+0x2b0),v['RELEASECYCLE'])
                self.assertEqual(h.get(a+0x50),1)
                events.append(tick)
                h.put(v['COOLDOWNT']+4,period)
            if h.get(a+0x2c0,2)==0:
                # Fixture supplies the next attack order; native code still
                # performs its entire reload, release and recoil animations.
                h.put(a+0x2c0,2,2); h.put(a+0x2b0,0)
        return events,h.get(a+0x362,2)

    def test_artillery_delay_preserves_firing_frame_and_ammunition(self):
        for extreme in [False,True]:
            for name,kind,frame,handler in [('Catapult',39,23,0x568320),
                    ('Trebuchet',40,27,0x569410),('Mangonel',41,22,0x56a3f0),
                    ('Tower ballista',61,12,0x56ecd0),('Fire ballista',77,13,0x577cc0)]:
                with self.subTest(extreme=extreme,unit=name):
                    setup=self.prepare(name,kind,frame,handler,extreme)
                    baseline,ammo=self.simulate(setup,kind,1)
                    self.assertGreaterEqual(len(baseline),2)
                    natural=max(b-a for a,b in zip(baseline,baseline[1:]))
                    period=natural+100
                    delayed,left=self.simulate(setup,kind,period,baseline[0]+2*period+20)
                    self.assertGreaterEqual(len(delayed),2)
                    self.assertEqual(baseline[0],delayed[0])
                    self.assertTrue(all(b-a==period for a,b in zip(delayed,delayed[1:])),delayed)
                    if kind in (39,40):
                        self.assertEqual(1000-ammo,len(baseline))
                        self.assertEqual(1000-left,len(delayed))

    def test_hold_gate_does_not_freeze_movement_cows_or_early_windup(self):
        setup=self.prepare('Catapult',39,23,0x568320,False)
        _,h,v,*_=setup
        a=h.unit(1,39)
        for off,value,size in [(0x2c0,4,2),(0x2b0,v['RELEASECYCLE']-1,4),(0x40,5,4),(0x44,5,4)]:
            h.put(a+off,value,size)
        def hold(remaining=100,blocked=0):
            return h.call(v['SHOULDHOLD'],[1,v['RELEASECYCLE'],remaining,blocked])
        self.assertEqual(hold(),1)
        self.assertEqual(hold(0),0)
        self.assertEqual(hold(0,1),1)
        h.put(a+0x2c0,8,2)
        self.assertEqual(hold(),0)
        h.put(a+0x2c0,4,2);h.put(a+0x3b0,1,2)
        self.assertEqual(hold(),0)
        h.put(a+0x3b0,0,2);h.put(a+0x40,3)
        self.assertEqual(hold(),0)

    def integrated(self, name, kind, handler, config, extreme=False):
        observer=projectile_tests.NativeTests()
        h=observer.prepare({name:config},extreme)
        a=h.unit(1,kind)
        h.unit(2,22,owner=2,x=44)
        for off,value,size in [(0x3b4,3 if kind==40 else 2,2),(0x362,1000,2),(0xbe,352,2),
                              (0xc0,320,2),(0x39c,3,2),(0x344,0xffff,2)]:
            h.put(a+off,value,size)
        animation=h.blobs['configuredAnimationHold'][2]['RESUME']-18
        handler+=h.v['FIREPROJ']-0x532700
        sound=0x449dc0+(0x2e0 if extreme else 0)
        def no_sound(h):
            esp=h.uc.reg_read(r.UC_X86_REG_ESP)
            h.uc.reg_write(r.UC_X86_REG_EIP,h.get(esp))
            h.uc.reg_write(r.UC_X86_REG_ESP,esp+16)
        def tick():
            queued=observer.tick(h,1)
            h.put(h.v['CURUNIT'],1)
            h.call(animation,registers={r.UC_X86_REG_ESI:h.v['UNITSTATE'],
                       r.UC_X86_REG_EBX:1,r.UC_X86_REG_EBP:0},stop=animation+0xa1)
            shots=[]
            h.call(handler,callbacks={h.spawner:observer.spawn_callback(shots),sound:no_sound})
            if shots:
                self.assertEqual(h.get(a+0x2b0),h.get(h.v['NATIVECYCLET']+kind*4))
                self.assertEqual(h.get(a+0x50),1)
            return queued,shots
        return h,a,tick

    def test_configured_artillery_interval_drives_native_release(self):
        for extreme in [False,True]:
            for name,kind,handler in [('Catapult',39,0x568320),
                    ('Trebuchet',40,0x569410),('Mangonel',41,0x56a3f0),
                    ('Tower ballista',61,0x56ecd0),('Fire ballista',77,0x577cc0)]:
                with self.subTest(extreme=extreme,unit=name):
                    # A long interval must be measured shot to shot; a short one
                    # cannot truncate the original engine's animation cycle.
                    gaps=[]
                    for interval in [400,1]:
                        h,a,tick=self.integrated(name,kind,handler,
                            {'interval':interval,'count':3,'projectile':'mangonel_pebble',
                             'sync_to_animation':True,'inaccuracy':0},extreme)
                        events=[]
                        for t in range(1100 if interval==400 else 700):
                            queued,shots=tick()
                            self.assertEqual(queued,[],'no independent timer shots')
                            if shots:
                                events.append(t)
                                self.assertEqual([s[9] for s in shots],[4]*3)
                        self.assertGreaterEqual(len(events),3 if interval==400 else 2,events)
                        delta=[b-a for a,b in zip(events,events[1:])]
                        if interval==400: self.assertEqual(set(delta),{400},events)
                        else:
                            frame={39:23,40:27,41:22,61:12,77:13}[kind]
                            native,_=self.simulate(self.prepare(name,kind,frame,handler,extreme),kind,1)
                            self.assertEqual(set(delta),{native[1]-native[0]},events)
                        gaps.append(delta)
                        if kind in (39,40): self.assertEqual(1000-h.get(a+0x362,2),len(events))

    def test_mangonel_interval_without_count_keeps_seven_projectiles(self):
        h,a,tick=self.integrated('Mangonel',41,0x56a3f0,{'interval':400})
        events=[]
        for t in range(600):
            queued,shots=tick()
            self.assertFalse(queued)
            if shots: events.append((t,len(shots)))
        self.assertGreaterEqual(len(events),2,events)
        self.assertTrue(all(n==7 for _,n in events),events)

    def test_native_release_waits_for_crew_and_target_without_charging_stones(self):
        for blocked in ['crew','target','stance']:
            with self.subTest(blocked=blocked):
                h,a,tick=self.integrated('Catapult',39,0x568320,
                    {'interval':250,'require_manned':2,'interval_moving':0})
                events=[]
                for t in range(530):
                    if t==300:
                        if blocked=='crew': h.put(a+0x3b4,0,2)
                        elif blocked=='target': h.put(h.base+2*0x490+0x3c8,0)
                        else: h.put(a+0xb6,328,2)
                    if 300<t<420 and blocked=='stance':
                        h.put(a+0xb6,320+(t%2)*8,2)
                    if t==420:
                        h.put(a+0x3b4,2,2);h.put(h.base+2*0x490+0x3c8,1000)
                    queued,shots=tick()
                    self.assertFalse(queued)
                    if shots: events.append(t)
                    if 300<=t<420: self.assertEqual(h.get(a+0x362,2),999)
                self.assertEqual(events[0],99)
                self.assertGreaterEqual(len(events),2,events)
                self.assertGreaterEqual(events[1],420,events)
                self.assertEqual(1000-h.get(a+0x362,2),len(events))

    def test_staggered_ai_cows_start_at_release_frame(self):
        h,a,tick=self.integrated('Catapult',39,0x568320,{'interval':250,
            'projectile':'mangonel_pebble','count':3,'ai_cow_vs_units':True,
            'cow_projectile':'arrow','cow_count':2,'stagger_min':5,'stagger_max':5})
        h.put(h.v['PLAYERAIC']+0x39f4,1);h.put(h.v['AICCOW']+0x2a4,1)
        events=[]
        for t in range(450):
            queued,shots=tick()
            if queued or shots: events.append((t,[s[9] for s in queued+shots]))
        self.assertEqual(events,[(99,[1]),(104,[1]),(349,[1]),(354,[1])])
        self.assertEqual(h.get(a+0x362,2),998)
        self.assertEqual(h.get(a+0x3b0,2),0)

    def test_loaded_release_restores_cooldown_polling_and_native_animation(self):
        observer=projectile_tests.NativeTests()
        h,a,tick=self.integrated('Catapult',39,0x568320,
            {'interval':250,'count':3,'stagger_max':3,'inaccuracy':8})
        for y in range(400): h.put(h.v['TILEROWS']+12*y,400*y)
        for _ in range(320): tick()
        handle=observer.state_handle(h);state=h.sections[b'projectileModifier']
        state.serialize(state,handle)
        native=bytes(h.uc.mem_read(a,0x490))
        first=[tick() for _ in range(65)]
        stones=h.get(a+0x362,2)
        h.uc.mem_write(a,native)  # game-owned animation/order state in its save
        state.deserialize(state,handle)
        second=[tick() for _ in range(65)]
        self.assertEqual(first,second)
        self.assertTrue(any(queued or shots for queued,shots in first))
        self.assertEqual(h.get(a+0x362,2),stones)
        handle[b'files'][b'format']=b'3'
        before=h.get(h.v['COOLDOWNT']+4)
        with self.assertRaisesRegex(Exception,'unsupported saved state format'):
            state.deserialize(state,handle)
        self.assertEqual(h.get(h.v['COOLDOWNT']+4),before)

    def test_no_target_polling_is_bounded_and_preload_changes_poll_rate(self):
        for preload,period in [(False,20),(True,5)]:
            h,a,tick=self.integrated('Catapult',39,0x568320,
                {'interval':250,'preload':preload})
            h.put(h.base+2*0x490+0x3c8,0)
            scans=[]
            from unicorn import UC_HOOK_CODE
            def count(uc,ip,size,data): scans.append(ip)
            token=h.uc.hook_add(UC_HOOK_CODE,count,begin=h.v['PICKTARGET'],end=h.v['PICKTARGET'])
            try:
                for _ in range(40): self.assertEqual(tick(),([],[]))
            finally: h.uc.hook_del(token)
            self.assertEqual(len(scans),40//period)
            self.assertEqual(h.get(a+0x362,2),1000)
