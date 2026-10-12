/*
 * Datos de prueba para el modo demo (?demo, o sin apiUrl en config.js).
 * Son los mismos datos falsos que usa el QA del repo privado. Nada aquí es
 * real: ni nombres, ni partidas, ni PINs (en el demo cualquier PIN entra).
 */
(function () {
  'use strict';
  const DEMO_TOKENS = { ts: {name:'Sofia', role:'member'}, ta: {name:'Hector', role:'admin'}, tg: {name:'Luis', role:'manager'} };
  const MOCK = {
    listNamesForLogin: () => ['Sofia','Hector','Luis'],
    login: (n) => n==='Hector' ? {ok:true,token:'ta',name:'Hector',role:'admin'} : (n==='Luis' ? {ok:true,token:'tg',name:'Luis',role:'manager'} : {ok:true,token:'ts',name:'Sofia',role:'member'}),
    logout: () => ({ok:true}),
    getDeckCatalog: () => ([
      {name:'Jujutsu Kaisen - Red',anime:'JJK',color:'Red',type:'Own'},
      {name:'Chainsaw Man - Blue',anime:'CSM',color:'Blue',type:'Own'},
      {name:'Titan Ramp',anime:'',color:'',type:'Rival'},
      {name:'Hunter Rush',anime:'',color:'',type:'Rival'}]),
    getRivalCatalog: () => (['Kenji','Lulu','Marco R.']),
    getActiveMemberNames: () => (['Sofia','Marco']),
    listMembersAdmin: () => ([
      {row:2,name:'Hector',hasPin:true,role:'admin',active:true},
      {row:3,name:'Luis',hasPin:true,role:'manager',active:true},
      {row:4,name:'Sofia',hasPin:true,role:'member',active:true,lockedMinutes:12}]),
    updateMemberRole: () => ({ok:true}),
    getWinRateByDeck: () => ([{deck:'Jujutsu Kaisen - Red',wins:14,total:21,winRate:67,
      bestMatchup:{rivalDeck:'Titan Ramp',wins:8,total:10,winRate:80},
      worstMatchup:{rivalDeck:'Hunter Rush',wins:2,total:8,winRate:25},
      firstTurn:{wins:7,total:10,winRate:70}, secondTurn:{wins:7,total:11,winRate:64}}]),
    getWinRateByRival: () => ({byRival:[
      {rival:'Kenji',wins:8,total:25,winRate:32,bestDeck:{deck:'Titan Ramp',wins:3,total:5,winRate:60},worstDeck:{deck:'Reze',wins:1,total:6,winRate:17}},
      {rival:'Lulu',wins:14,total:18,winRate:78,bestDeck:{deck:'Hunter Rush',wins:5,total:5,winRate:100},worstDeck:null}],
      bestRival:{rival:'Lulu',wins:14,total:18,winRate:78}, worstRival:{rival:'Kenji',wins:8,total:25,winRate:32}}),
    getMatchHistory: (tok,deck,off,lim,rival,name) => ({_deck:deck,_rival:rival,_name:name,todayKey:'09/06/2026',yesterdayKey:'09/05/2026',items:[
      {id:'m1',date:'09/06/2026 12:00',player:'Sofia',ownDeck:'Jujutsu Kaisen - Red',rivalDeck:'Titan Ramp',result:'Win',turn:'First',rivalName:'Kenji'},
      {id:'m2',date:'09/05/2026 18:00',player:'Sofia',ownDeck:'Jujutsu Kaisen - Red',rivalDeck:'Hunter Rush',result:'Loss',turn:'',rivalName:''}]
      .filter(m => !name || name === 'All' || m.rivalName === String(name)), hasMore:false}),
    getTeamMatchHistory: (tok,pl,deck,off,lim,rival,name) => ({_pl:pl,_deck:deck,_rival:rival,_name:name,items:[],hasMore:false}),
    getTeamDashboard: () => ({totalMatches:47, teamWinRate:58, dateRange:{from:'Sep 1, 2026',to:'Sep 6, 2026'},
      byDeck:[{deck:'Jujutsu Kaisen - Red',wins:13,total:21,winRate:62,
        bestMatchup:{rivalDeck:'Titan Ramp',wins:8,total:10,winRate:80},
        worstMatchup:{rivalDeck:'Hunter Rush',wins:3,total:10,winRate:30},
        firstTurn:{wins:7,total:10,winRate:70}, secondTurn:{wins:6,total:11,winRate:55}}],
      byMember:[{player:'Sofia',wins:12,total:18,winRate:67}], byMemberDeck:[], rivalMeta:[],
      byRival:[{rival:'Kenji',wins:8,total:25,winRate:32,bestDeck:null,worstDeck:null},
               {rival:'Lulu',wins:14,total:18,winRate:78,bestDeck:null,worstDeck:null}],
      bestRival:{rival:'Lulu',wins:14,total:18,winRate:78}, worstRival:{rival:'Kenji',wins:8,total:25,winRate:32},
      brick:{coverage:{marked:40,total:47,pct:85},
        overall:{marked:40,bricks:9,brickRate:23,rivalBricks:7,rivalBrickRate:18,
          withBrick:{wins:3,total:9,winRate:33}, withoutBrick:{wins:21,total:31,winRate:68}},
        byDeck:[{deck:'Jujutsu Kaisen - Red',marked:28,bricks:7,brickRate:25,rivalBricks:5,rivalBrickRate:18,
          withBrick:{wins:2,total:7,winRate:29}, withoutBrick:{wins:14,total:21,winRate:67}}],
        byMember:[{player:'Sofia',marked:24,bricks:6,brickRate:25},
                  {player:'Marco',marked:16,bricks:3,brickRate:19}]}}),
    getTeamRivalStats: (tok,who) => (who==='Sofia'
      ? {byRival:[{rival:'Kenji',wins:5,total:6,winRate:83,bestDeck:null,worstDeck:null}],bestRival:null,worstRival:null}
      : {byRival:[{rival:'Lulu',wins:1,total:4,winRate:25,bestDeck:null,worstDeck:null}],bestRival:null,worstRival:null}),
    getFacedRivalDecks: (tok, who) => (who==='Marco' ? ['Titan Ramp'] : ['Titan Ramp','Hunter Rush','Reze']),
    getBrickStats: () => ({
      coverage:{marked:18,total:21,pct:86},
      overall:{marked:18,bricks:5,brickRate:28,rivalBricks:3,rivalBrickRate:17,
        withBrick:{wins:1,total:5,winRate:20}, withoutBrick:{wins:9,total:13,winRate:69}},
      byDeck:[
        {deck:'Jujutsu Kaisen - Red',marked:13,bricks:4,brickRate:31,rivalBricks:2,rivalBrickRate:15,
         withBrick:{wins:1,total:4,winRate:25}, withoutBrick:{wins:6,total:9,winRate:67}},
        {deck:'Chainsaw Man - Blue',marked:5,bricks:1,brickRate:20,rivalBricks:1,rivalBrickRate:20,
         withBrick:null, withoutBrick:{wins:3,total:4,winRate:75}}],
      byMember:[]}),
    getTeamBrickStats: () => ({coverage:{marked:40,total:47,pct:85},
      overall:{marked:40,bricks:9,brickRate:23,rivalBricks:7,rivalBrickRate:18,
        withBrick:{wins:3,total:9,winRate:33}, withoutBrick:{wins:21,total:31,winRate:68}},
      byDeck:[], byMember:[]}),
    getMemberScreen: (tok, deckFilter, rivalFilter, includeCatalog) => {
      const out = {
        player: 'Sofia',
        byDeck: MOCK.getWinRateByDeck(),
        rival: MOCK.getWinRateByRival(),
        history: MOCK.getMatchHistory(tok, deckFilter, 0, 20, rivalFilter),
        facedRivalDecks: MOCK.getFacedRivalDecks(tok, 'Sofia'),
        recent: MOCK.getRecent('Sofia'),
      };
      if (includeCatalog !== false) {
        out.catalog = MOCK.getDeckCatalog();
        out.rivalNames = MOCK.getRivalCatalog();
      }
      return out;
    },
    registerMatch: () => ({ok:true, id:'new', catalogChanged:false}),
    adminRegisterMatchForMember: () => ({ok:true, id:'new-adm', catalogChanged:false}),
    editMatch: () => ({ok:true, catalogChanged:false}),
    deleteMatch: () => ({ok:true}),
    undoMatch: () => ({ok:true, catalogChanged:false, removedDeck:null, removedName:null}),
    addOwnDeck: (tok, name) => ({ok:true, name:name}),
    updateMember: (tok, row, name, pin) => ({ok:true, pinChanged: !!pin}),
    deactivateMember: () => ({ok:true}),
    reactivateMember: () => ({ok:true}),
    addMember: () => ({ok:true}),
    resumeSession: (t) => (DEMO_TOKENS[t] ? Object.assign({ok:true}, DEMO_TOKENS[t]) : {ok:false}),
    getRecent: (player) => ({decks:['Jujutsu Kaisen - Red'], rivalDecks:['Titan Ramp','Hunter Rush'], rivalNames:['Kenji','Lulu'],
      deckCounts:{'Jujutsu Kaisen - Red':21}, today:['W','W','L'], last10:['W','W','L','W','W','L','W','W','L','W'], weekCount:6}),
    getLogContext: (tok, player) => MOCK.getRecent(player),
    findPossibleDuplicateDecks: () => ([]),
    findPossibleDuplicateRivalNames: () => ([]),
    previewCatalogSpellingRepair: () => ({total:0, changes:[]}),
    unlockMember: () => ({ok:true}),
    updateDeck: (tok, orig, name) => ({ok:true, renamed: orig !== name}),
    removeDeck: () => ({ok:true}),
    mergeDecks: () => ({ok:true, rowsUpdated:3, backupName:null}),
    updateRivalName: (tok, orig, name) => ({ok:true, renamed: orig !== name}),
    removeRivalName: () => ({ok:true}),
    mergeRivalNames: () => ({ok:true, rowsUpdated:2, backupName:null}),
    generateTeamReportPdf: () => { throw new Error('the PDF report is not available in the demo'); },
    applyCatalogSpellingRepair: () => ({ok:true, rowsUpdated:0, backupName:null}),
  };
  window.UAT_DEMO = MOCK;
})();
