import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

void main() => runApp(const DhanLaxmiApp());
const gold = Color(0xFFFFD979),
    violet = Color(0xFF8B5CF6),
    ink = Color(0xFF090A12);
const defaultWalletTopUpLink =
    'upi://pay?pa=9509961818%40ybl&pn=DhanLaxmi&cu=INR&tn=Wallet%20top-up';

class ApiClient {
  ApiClient({String? base})
      : base = base ??
            const String.fromEnvironment('API_BASE_URL',
                defaultValue: 'https://overhaul-oaf-silk.ngrok-free.dev');
  final String base;
  final storage = const FlutterSecureStorage();
  Future<Map<String, dynamic>> get(String path) async {
    final t = await storage.read(key: 'access');
    final r = await http.get(Uri.parse('$base$path'),
        headers: {if (t != null) 'Authorization': 'Bearer $t'});
    if (r.statusCode >= 400) {
      throw Exception(jsonDecode(r.body)['detail'] ?? 'Request failed');
    }
    return jsonDecode(r.body);
  }

  Future<Map<String, dynamic>> post(
      String path, Map<String, dynamic> body) async {
    final r = await http.post(Uri.parse('$base$path'),
        headers: {'Content-Type': 'application/json'}, body: jsonEncode(body));
    final data = jsonDecode(r.body) as Map<String, dynamic>;
    if (r.statusCode >= 400) {
      throw Exception(data['detail'] ?? 'Request failed');
    }
    return data;
  }

  Future<Map<String, dynamic>> put(
      String path, Map<String, dynamic> body) async {
    final t = await storage.read(key: 'access');
    final r = await http.put(Uri.parse('$base$path'),
        headers: {
          'Content-Type': 'application/json',
          if (t != null) 'Authorization': 'Bearer $t'
        },
        body: jsonEncode(body));
    final data = jsonDecode(r.body) as Map<String, dynamic>;
    if (r.statusCode >= 400) {
      throw Exception(data['detail'] ?? 'Request failed');
    }
    return data;
  }
}

class Lottery {
  Lottery(this.title, this.description, this.price, this.prize, this.deadline,
      this.image);
  final String title, description, prize, image;
  final int price;
  final DateTime deadline;
  factory Lottery.fromJson(Map<String, dynamic> x) => Lottery(
      x['name'] ?? 'Lottery',
      x['description'] ?? '',
      (x['entry_price'] as num).round(),
      'First Prize',
      DateTime.parse(x['join_deadline']),
      x['banner_url'] ?? 'https://picsum.photos/seed/lottery/1200/700');
}

final samples = [
  Lottery(
      'Mega Bike Lottery',
      'Ride home a Royal Enfield',
      100,
      'Royal Enfield',
      DateTime(2026, 8, 20, 20),
      'https://images.unsplash.com/photo-1558981806-ec527fa84c39?w=1200'),
  Lottery(
      'Mega Car Lottery',
      'Your dream drive is one ticket away',
      500,
      'Premium Car',
      DateTime(2026, 8, 28, 20),
      'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=1200')
];

class DhanLaxmiApp extends StatelessWidget {
  const DhanLaxmiApp({super.key});
  @override
  Widget build(BuildContext c) => MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'DhanLaxmi',
      theme: ThemeData(
          brightness: Brightness.dark,
          scaffoldBackgroundColor: ink,
          colorScheme: const ColorScheme.dark(
              primary: gold, secondary: violet, surface: Color(0xFF13141F)),
          textTheme:
              GoogleFonts.plusJakartaSansTextTheme(ThemeData.dark().textTheme),
          filledButtonTheme: FilledButtonThemeData(
              style: FilledButton.styleFrom(
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16)),
                  minimumSize: const Size(0, 54))),
          inputDecorationTheme: InputDecorationTheme(
              filled: true,
              fillColor: Colors.white.withValues(alpha: .055),
              border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide.none),
              enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: const BorderSide(color: Colors.white10)),
              focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: const BorderSide(color: gold))),
          navigationBarTheme: NavigationBarThemeData(
              backgroundColor: const Color(0xF20E0F18),
              indicatorColor: violet.withValues(alpha: .25),
              labelTextStyle: WidgetStateProperty.resolveWith(
                  (s) => TextStyle(fontSize: 11, fontWeight: s.contains(WidgetState.selected) ? FontWeight.w800 : FontWeight.w500, color: s.contains(WidgetState.selected) ? Colors.white : Colors.white54))),
          cardTheme: const CardThemeData(color: Color(0xFF141521), surfaceTintColor: Colors.transparent)),
      home: const AuthGate());
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});
  @override
  Widget build(BuildContext context) => FutureBuilder<String?>(
      future: const FlutterSecureStorage().read(key: 'access'),
      builder: (_, snapshot) => snapshot.connectionState != ConnectionState.done
          ? const Scaffold(body: Center(child: CircularProgressIndicator()))
          : snapshot.data != null
              ? const Shell()
              : const AuthPage());
}

class AuthPage extends StatefulWidget {
  const AuthPage({super.key});
  @override
  State<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends State<AuthPage> {
  bool register = false, loading = false, showPassword = false;
  final name = TextEditingController(),
      mobile = TextEditingController(),
      password = TextEditingController(),
      confirmPassword = TextEditingController(),
      referral = TextEditingController();
  String? error;
  Future<void> submit() async {
    if (mobile.text.trim().length < 10) {
      setState(() => error = 'Enter a valid 10-digit mobile number.');
      return;
    }
    if (password.text.length < 8) {
      setState(() => error = 'Password must be at least 8 characters.');
      return;
    }
    if (register && name.text.trim().length < 2) {
      setState(() => error = 'Please enter your full name.');
      return;
    }
    if (register && password.text != confirmPassword.text) {
      setState(() => error = 'Passwords do not match.');
      return;
    }
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final api = ApiClient();
      final result = await api.post(
          register ? '/api/auth/register' : '/api/auth/login',
          register
              ? {
                  'full_name': name.text.trim(),
                  'mobile': mobile.text.trim(),
                  'password': password.text,
                  if (referral.text.trim().isNotEmpty)
                    'referral_code': referral.text.trim()
                }
              : {'mobile': mobile.text.trim(), 'password': password.text});
      await api.storage
          .write(key: 'access', value: result['data']['access_token']);
      await api.storage
          .write(key: 'refresh', value: result['data']['refresh_token']);
      if (mounted) {
        Navigator.pushReplacement(
            context, MaterialPageRoute(builder: (_) => const Shell()));
      }
    } catch (e) {
      setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      body: Container(
          decoration: const BoxDecoration(
              gradient: RadialGradient(
                  center: Alignment.topCenter,
                  radius: 1.2,
                  colors: [Color(0xFF24183F), ink])),
          child: SafeArea(
              child: Center(
                  child: SingleChildScrollView(
                      padding: const EdgeInsets.all(22),
                      child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 440),
                          child: Container(
                              padding:
                                  const EdgeInsets.fromLTRB(26, 28, 26, 24),
                              decoration: BoxDecoration(
                                  color: const Color(0xDD11121D),
                                  borderRadius: BorderRadius.circular(28),
                                  border: Border.all(color: Colors.white10),
                                  boxShadow: const [
                                    BoxShadow(
                                        color: Colors.black45,
                                        blurRadius: 40,
                                        offset: Offset(0, 18))
                                  ]),
                              child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [
                                    Center(
                                        child: Container(
                                            width: 64,
                                            height: 64,
                                            decoration: BoxDecoration(
                                                gradient: const LinearGradient(
                                                    colors: [
                                                      gold,
                                                      Color(0xFFFFB74D)
                                                    ]),
                                                borderRadius:
                                                    BorderRadius.circular(20)),
                                            child: const Icon(
                                                Icons.auto_awesome,
                                                color: ink,
                                                size: 31))),
                                    const SizedBox(height: 20),
                                    Text(
                                        register
                                            ? 'Create your account'
                                            : 'Welcome back',
                                        textAlign: TextAlign.center,
                                        style: const TextStyle(
                                            fontSize: 30,
                                            fontWeight: FontWeight.w900)),
                                    const SizedBox(height: 8),
                                    Text(
                                        register
                                            ? 'Register to receive your unique referral code.'
                                            : 'Sign in to enter transparent draws.',
                                        textAlign: TextAlign.center,
                                        style: const TextStyle(
                                            color: Colors.white54)),
                                    const SizedBox(height: 26),
                                    if (register)
                                      authField(name, 'Full name',
                                          Icons.person_outline),
                                    authField(mobile, 'Mobile number',
                                        Icons.phone_outlined,
                                        keyboard: TextInputType.phone),
                                    authField(password, 'Password',
                                        Icons.lock_outline,
                                        obscure: true),
                                    if (register)
                                      authField(
                                          confirmPassword,
                                          'Confirm password',
                                          Icons.verified_user_outlined,
                                          obscure: true),
                                    if (register)
                                      authField(
                                          referral,
                                          'Referral code (optional)',
                                          Icons.group_add_outlined),
                                    if (error != null)
                                      Padding(
                                          padding:
                                              const EdgeInsets.only(bottom: 12),
                                          child: Text(error!,
                                              style: const TextStyle(
                                                  color: Colors.redAccent))),
                                    SizedBox(
                                        height: 54,
                                        child: FilledButton(
                                            onPressed: loading ? null : submit,
                                            style: FilledButton.styleFrom(
                                                backgroundColor: gold,
                                                foregroundColor: ink),
                                            child: loading
                                                ? const SizedBox.square(
                                                    dimension: 20,
                                                    child:
                                                        CircularProgressIndicator(
                                                            strokeWidth: 2))
                                                : Text(
                                                    register
                                                        ? 'Register'
                                                        : 'Login',
                                                    style: const TextStyle(
                                                        fontWeight:
                                                            FontWeight.w900)))),
                                    const SizedBox(height: 12),
                                    TextButton(
                                        onPressed: () => setState(() {
                                              register = !register;
                                              error = null;
                                            }),
                                        child: Text(register
                                            ? 'Already registered? Login'
                                            : 'New user? Create account'))
                                  ]))))))));
  Widget authField(TextEditingController c, String label, IconData icon,
          {bool obscure = false, TextInputType? keyboard}) =>
      Padding(
          padding: const EdgeInsets.only(bottom: 13),
          child: TextField(
              controller: c,
              obscureText: obscure && !showPassword,
              keyboardType: keyboard,
              decoration: InputDecoration(
                  labelText: label,
                  prefixIcon: Icon(icon),
                  suffixIcon: obscure
                      ? IconButton(
                          onPressed: () =>
                              setState(() => showPassword = !showPassword),
                          icon: Icon(showPassword
                              ? Icons.visibility_off_outlined
                              : Icons.visibility_outlined))
                      : null,
                  filled: true,
                  fillColor: Colors.white.withValues(alpha: .05),
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: BorderSide.none))));
}

class Shell extends StatefulWidget {
  const Shell({super.key});
  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  int tab = 0;
  final pages = const [
    Home(),
    MyTicketsPage(),
    WalletPage(),
    WinnersPage(),
    ProfilePage()
  ];
  @override
  Widget build(BuildContext c) => Scaffold(
      body: IndexedStack(index: tab, children: pages),
      bottomNavigationBar: NavigationBar(
          height: 72,
          backgroundColor: const Color(0xFF0E0F18),
          indicatorColor: violet.withValues(alpha: .28),
          selectedIndex: tab,
          onDestinationSelected: (i) => setState(() => tab = i),
          destinations: const [
            NavigationDestination(
                icon: Icon(Icons.home_outlined),
                selectedIcon: Icon(Icons.home),
                label: 'Home'),
            NavigationDestination(
                icon: Icon(Icons.confirmation_number_outlined),
                label: 'Tickets'),
            NavigationDestination(
                icon: Icon(Icons.account_balance_wallet_outlined),
                label: 'Wallet'),
            NavigationDestination(
                icon: Icon(Icons.emoji_events_outlined), label: 'Winners'),
            NavigationDestination(
                icon: Icon(Icons.person_outline), label: 'Profile')
          ]));
}

class Home extends StatefulWidget {
  const Home({super.key});
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  List<Lottery> lotteries = samples;
  bool hasUnreadNotifications = false;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final api = ApiClient();
      final result = await api.get('/api/lotteries');
      final live =
          (result['data'] as List).map((x) => Lottery.fromJson(x)).toList();
      if (mounted && live.isNotEmpty) setState(() => lotteries = live);
      final notifications = await api.get('/api/notifications');
      final unread = (notifications['data'] as List)
          .any((item) => item['is_read'] != true);
      if (mounted) setState(() => hasUnreadNotifications = unread);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext c) => SafeArea(
          child: CustomScrollView(slivers: [
        SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 16),
            sliver: SliverToBoxAdapter(
                child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                  const Row(children: [
                    _BrandMark(),
                    SizedBox(width: 12),
                    Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('DHANLAXMI',
                              style: TextStyle(
                                  color: gold,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w900,
                                  letterSpacing: 2)),
                          SizedBox(height: 3),
                          Text('Make today lucky',
                              style: TextStyle(
                                  fontSize: 20, fontWeight: FontWeight.w800))
                        ])
                  ]),
                  InkWell(
                      borderRadius: BorderRadius.circular(14),
                      onTap: () async {
                        await Navigator.push(
                            c,
                            MaterialPageRoute(
                                builder: (_) => const NotificationsPage()));
                        load();
                      },
                      child: Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: .06),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: Colors.white10)),
                          child: Badge(
                              isLabelVisible: hasUnreadNotifications,
                              smallSize: 7,
                              backgroundColor: gold,
                              child: const Icon(
                                  Icons.notifications_none_rounded,
                                  color: Colors.white))))
                ]))),
        SliverToBoxAdapter(child: HeroBanner(lottery: lotteries.first)),
        SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 0),
            sliver: SliverToBoxAdapter(
                child: Row(children: [
              _QuickStat(
                  icon: Icons.verified_user_outlined,
                  label: 'Fair draws',
                  value: '100%'),
              SizedBox(width: 10),
              _QuickStat(
                  icon: Icons.bolt_rounded,
                  label: 'Live draws',
                  value: '${lotteries.length}'),
              SizedBox(width: 10),
              const _QuickStat(
                  icon: Icons.lock_outline_rounded,
                  label: 'Payments',
                  value: 'Secure')
            ]))),
        const SliverPadding(
            padding: EdgeInsets.fromLTRB(20, 26, 20, 12),
            sliver: SliverToBoxAdapter(
                child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                  Text('Active lotteries',
                      style:
                          TextStyle(fontSize: 19, fontWeight: FontWeight.w800)),
                  Text('View all', style: TextStyle(color: gold))
                ]))),
        SliverList.builder(
            itemCount: lotteries.length,
            itemBuilder: (c, i) => LotteryCard(lottery: lotteries[i])),
        const SliverToBoxAdapter(child: SizedBox(height: 30))
      ]));
}

class HeroBanner extends StatelessWidget {
  const HeroBanner({super.key, required this.lottery});
  final Lottery lottery;
  @override
  Widget build(BuildContext c) => Container(
      height: 285,
      margin: const EdgeInsets.symmetric(horizontal: 20),
      decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
                color: violet.withValues(alpha: .22),
                blurRadius: 32,
                offset: const Offset(0, 16))
          ],
          image: DecorationImage(
              image: NetworkImage(lottery.image), fit: BoxFit.cover)),
      child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(28),
              gradient: const LinearGradient(
                  begin: Alignment.topRight,
                  end: Alignment.bottomLeft,
                  colors: [Color(0x15000000), Color(0xEE090A12)])),
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                        color: gold, borderRadius: BorderRadius.circular(20)),
                    child: const Text('FEATURED DRAW',
                        style: TextStyle(
                            color: ink,
                            fontSize: 10,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 1))),
                const SizedBox(height: 11),
                Text(lottery.title,
                    style: const TextStyle(
                        fontSize: 29,
                        height: 1.05,
                        fontWeight: FontWeight.w900)),
                const SizedBox(height: 6),
                Text('${lottery.description} • Entry ₹${lottery.price}',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white70)),
                const SizedBox(height: 16),
                FilledButton(
                    onPressed: () => showModalBottomSheet(
                        context: c,
                        isScrollControlled: true,
                        backgroundColor: Colors.transparent,
                        builder: (_) => JoinSheet(lottery: lottery)),
                    style: FilledButton.styleFrom(
                        backgroundColor: gold, foregroundColor: ink),
                    child: Text('Enter for ₹${lottery.price}'))
              ])));
}

class LotteryCard extends StatelessWidget {
  const LotteryCard({super.key, required this.lottery});
  final Lottery lottery;
  @override
  Widget build(BuildContext c) => InkWell(
      onTap: () => Navigator.push(
          c, MaterialPageRoute(builder: (_) => Details(lottery: lottery))),
      child: Container(
          margin: const EdgeInsets.fromLTRB(20, 0, 20, 13),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
              gradient: LinearGradient(colors: [
                Colors.white.withValues(alpha: .075),
                Colors.white.withValues(alpha: .025)
              ]),
              border: Border.all(color: Colors.white10),
              borderRadius: BorderRadius.circular(20)),
          child: Row(children: [
            ClipRRect(
                borderRadius: BorderRadius.circular(15),
                child: Image.network(lottery.image,
                    width: 108,
                    height: 118,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) => Container(
                        width: 108,
                        height: 118,
                        color: const Color(0xFF242536),
                        child: const Icon(Icons.image_outlined,
                            color: Colors.white38)))),
            const SizedBox(width: 16),
            Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                  Text(lottery.title,
                      style: const TextStyle(
                          fontWeight: FontWeight.w800, fontSize: 16)),
                  const SizedBox(height: 7),
                  Row(children: [
                    Container(
                        width: 7,
                        height: 7,
                        decoration: const BoxDecoration(
                            color: Color(0xFF63E6A6), shape: BoxShape.circle)),
                    const SizedBox(width: 7),
                    const Text('Entries open',
                        style: TextStyle(
                            color: Color(0xFF8CE9BC),
                            fontSize: 12,
                            fontWeight: FontWeight.w700))
                  ]),
                  const SizedBox(height: 15),
                  Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('ENTRY',
                                  style: TextStyle(
                                      fontSize: 9,
                                      color: Colors.white38,
                                      letterSpacing: 1)),
                              Text('₹${lottery.price}',
                                  style: const TextStyle(
                                      color: gold,
                                      fontSize: 18,
                                      fontWeight: FontWeight.w900))
                            ]),
                        Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                                color: violet.withValues(alpha: .22),
                                borderRadius: BorderRadius.circular(10)),
                            child: const Icon(Icons.arrow_forward_rounded,
                                size: 18, color: Colors.white))
                      ])
                ]))
          ])));
}

class _BrandMark extends StatelessWidget {
  const _BrandMark();
  @override
  Widget build(BuildContext context) => Container(
      width: 42,
      height: 42,
      decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [gold, Color(0xFFFFA94D)]),
          borderRadius: BorderRadius.circular(13)),
      child: const Icon(Icons.auto_awesome, color: ink, size: 22));
}

class _QuickStat extends StatelessWidget {
  const _QuickStat(
      {required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label, value;
  @override
  Widget build(BuildContext context) => Expanded(
      child: Container(
          padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 10),
          decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .04),
              border: Border.all(color: Colors.white10),
              borderRadius: BorderRadius.circular(16)),
          child: Column(children: [
            Icon(icon, size: 18, color: gold),
            const SizedBox(height: 7),
            Text(value,
                style:
                    const TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
            const SizedBox(height: 2),
            Text(label,
                style: const TextStyle(fontSize: 9, color: Colors.white38))
          ])));
}

class Details extends StatelessWidget {
  const Details({super.key, required this.lottery});
  final Lottery lottery;
  @override
  Widget build(BuildContext c) => Scaffold(
      body: CustomScrollView(slivers: [
        SliverAppBar(
            expandedHeight: 310,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
                background: Image.network(lottery.image, fit: BoxFit.cover))),
        SliverPadding(
            padding: const EdgeInsets.all(22),
            sliver: SliverList.list(children: [
              Text(lottery.title,
                  style: const TextStyle(
                      fontSize: 29, fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              Text(lottery.description,
                  style: const TextStyle(color: Colors.white60, fontSize: 16)),
              const SizedBox(height: 24),
              const PrizeRow(),
              const SizedBox(height: 28),
              const Text('How it works',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
              const SizedBox(height: 15),
              ...[
                'Select your lottery',
                'Pay through your UPI app',
                'Receive a unique ticket',
                'Wait for the transparent draw',
                'Winners are announced automatically'
              ].asMap().entries.map((e) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: CircleAvatar(
                      radius: 15,
                      backgroundColor: violet.withValues(alpha: .2),
                      child: Text('${e.key + 1}',
                          style: const TextStyle(
                              fontSize: 12, color: Colors.white))),
                  title: Text(e.value))),
              const SizedBox(height: 100)
            ]))
      ]),
      bottomSheet: SafeArea(
          child: Padding(
              padding: const EdgeInsets.all(14),
              child: SizedBox(
                  width: double.infinity,
                  height: 54,
                  child: FilledButton(
                      onPressed: () => showModalBottomSheet(
                          context: c,
                          isScrollControlled: true,
                          backgroundColor: Colors.transparent,
                          builder: (_) => JoinSheet(lottery: lottery)),
                      style: FilledButton.styleFrom(
                          backgroundColor: gold, foregroundColor: ink),
                      child: Text('Join lottery • ₹${lottery.price}',
                          style: const TextStyle(
                              fontWeight: FontWeight.w900)))))));
}

class PrizeRow extends StatelessWidget {
  const PrizeRow({super.key});
  @override
  Widget build(BuildContext c) => Row(children: [
        for (final x in [('1st', 'Bike'), ('2nd', '₹25K'), ('3rd', '₹10K')])
          Expanded(
              child: Container(
                  margin: const EdgeInsets.only(right: 8),
                  padding: const EdgeInsets.all(13),
                  decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: .05),
                      borderRadius: BorderRadius.circular(14)),
                  child: Column(children: [
                    Text(x.$1,
                        style: const TextStyle(color: gold, fontSize: 12)),
                    const SizedBox(height: 6),
                    Text(x.$2,
                        style: const TextStyle(fontWeight: FontWeight.w800))
                  ])))
      ]);
}

class JoinSheet extends StatelessWidget {
  const JoinSheet({super.key, required this.lottery});
  final Lottery lottery;
  @override
  Widget build(BuildContext c) => Container(
      padding:
          EdgeInsets.fromLTRB(24, 12, 24, 24 + MediaQuery.paddingOf(c).bottom),
      decoration: const BoxDecoration(
          color: Color(0xFF151622),
          borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Container(
            width: 42,
            height: 4,
            decoration: BoxDecoration(
                color: Colors.white24, borderRadius: BorderRadius.circular(4))),
        const SizedBox(height: 22),
        const Icon(Icons.lock_outline, color: gold, size: 35),
        const SizedBox(height: 12),
        const Text('Secure UPI payment',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
        const SizedBox(height: 20),
        line('Entry fee', '₹${lottery.price}'),
        line('Wallet credit', '₹0'),
        const Divider(height: 28),
        line('Amount payable', '₹${lottery.price}', strong: true),
        const SizedBox(height: 22),
        SizedBox(
            width: double.infinity,
            height: 54,
            child: FilledButton(
                onPressed: () {
                  Navigator.pop(c);
                  ScaffoldMessenger.of(c).showSnackBar(const SnackBar(
                      content: Text(
                          'Connect your account to initiate UPI payment. Status is verified by the backend.')));
                },
                style: FilledButton.styleFrom(
                    backgroundColor: gold, foregroundColor: ink),
                child: Text('Pay ₹${lottery.price}',
                    style: const TextStyle(fontWeight: FontWeight.w900)))),
        const SizedBox(height: 12),
        const Text(
            'A ticket is created only after a signed provider confirmation.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white38, fontSize: 12))
      ]));
  Widget line(String a, String b, {bool strong = false}) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(a,
            style: TextStyle(color: strong ? Colors.white : Colors.white60)),
        Text(b,
            style: TextStyle(
                fontWeight: strong ? FontWeight.w900 : FontWeight.w600,
                fontSize: strong ? 19 : 14))
      ]));
}

class MyTicketsPage extends StatefulWidget {
  const MyTicketsPage({super.key});
  @override
  State<MyTicketsPage> createState() => _MyTicketsPageState();
}

class _MyTicketsPageState extends State<MyTicketsPage> {
  late Future<Map<String, dynamic>> future;
  @override
  void initState() {
    super.initState();
    future = ApiClient().get('/api/tickets');
  }

  @override
  Widget build(BuildContext context) => SafeArea(
      child: Padding(
          padding: const EdgeInsets.all(20),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('My Tickets',
                style: TextStyle(fontSize: 29, fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            const Text('All your verified lottery entries',
                style: TextStyle(color: Colors.white54)),
            const SizedBox(height: 22),
            Expanded(
                child: FutureBuilder<Map<String, dynamic>>(
                    future: future,
                    builder: (_, s) {
                      if (s.connectionState != ConnectionState.done) {
                        return const Center(child: CircularProgressIndicator());
                      }
                      final rows = (s.data?['data'] as List?) ?? [];
                      if (rows.isEmpty) {
                        return const EmptyPage(
                            icon: Icons.confirmation_number_outlined,
                            title: 'Your ticket wallet is empty',
                            text:
                                'Join an active draw and your verified ticket will appear here.');
                      }
                      return ListView.builder(
                          itemCount: rows.length,
                          itemBuilder: (_, i) {
                            final x = rows[i];
                            return Container(
                                margin: const EdgeInsets.only(bottom: 14),
                                padding: const EdgeInsets.all(18),
                                decoration: BoxDecoration(
                                    gradient: LinearGradient(colors: [
                                      violet.withValues(alpha: .2),
                                      Colors.white.withValues(alpha: .035)
                                    ]),
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(color: Colors.white10)),
                                child: Row(children: [
                                  Container(
                                      width: 46,
                                      height: 46,
                                      decoration: BoxDecoration(
                                          color: gold.withValues(alpha: .14),
                                          borderRadius:
                                              BorderRadius.circular(14)),
                                      child: const Icon(
                                          Icons.confirmation_number_rounded,
                                          color: gold)),
                                  const SizedBox(width: 14),
                                  Expanded(
                                      child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                        Text(x['ticket_number'],
                                            style: const TextStyle(
                                                fontWeight: FontWeight.w800)),
                                        const SizedBox(height: 5),
                                        Text(
                                            'Entry ₹${x['entry_amount']} • ${x['status']}',
                                            style: const TextStyle(
                                                color: Colors.white54,
                                                fontSize: 12))
                                      ])),
                                  const Icon(Icons.chevron_right,
                                      color: Colors.white30)
                                ]));
                          });
                    }))
          ])));
}

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({super.key});
  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  late Future<Map<String, dynamic>> future;
  @override
  void initState() {
    super.initState();
    future = ApiClient().get('/api/notifications');
  }

  Future<void> _refresh() async {
    setState(() => future = ApiClient().get('/api/notifications'));
    await future;
  }

  Future<void> _markRead(Map<String, dynamic> item) async {
    if (item['is_read'] != true) {
      await ApiClient().put('/api/notifications/${item['id']}/read', {});
      await _refresh();
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: FutureBuilder<Map<String, dynamic>>(
          future: future,
          builder: (_, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return EmptyPage(
                  icon: Icons.cloud_off_outlined,
                  title: 'Unable to load notifications',
                  text: snapshot.error
                      .toString()
                      .replaceFirst('Exception: ', ''));
            }
            final rows = (snapshot.data?['data'] as List?) ?? [];
            if (rows.isEmpty) {
              return const EmptyPage(
                  icon: Icons.notifications_none_rounded,
                  title: 'No notifications yet',
                  text:
                      'Ticket confirmations and draw updates will appear here.');
            }
            return RefreshIndicator(
                onRefresh: _refresh,
                child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: rows.length,
                    itemBuilder: (_, i) {
                      final item = rows[i] as Map<String, dynamic>;
                      final unread = item['is_read'] != true;
                      return Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          child: ListTile(
                              onTap: () => _markRead(item),
                              contentPadding: const EdgeInsets.all(14),
                              leading: CircleAvatar(
                                  backgroundColor:
                                      (unread ? gold : Colors.white)
                                          .withValues(alpha: .12),
                                  child: Icon(Icons.notifications_rounded,
                                      color: unread ? gold : Colors.white54)),
                              title: Text(item['title'] ?? 'Notification',
                                  style: TextStyle(
                                      fontWeight: unread
                                          ? FontWeight.w900
                                          : FontWeight.w600)),
                              subtitle: Padding(
                                  padding: const EdgeInsets.only(top: 6),
                                  child: Text(item['body'] ?? '',
                                      style: const TextStyle(
                                          color: Colors.white60))),
                              trailing: unread
                                  ? const CircleAvatar(
                                      radius: 4, backgroundColor: gold)
                                  : const Icon(Icons.done,
                                      size: 18, color: Colors.white30)));
                    }));
          }));
}

class WalletPage extends StatefulWidget {
  const WalletPage({super.key});
  @override
  State<WalletPage> createState() => _WalletPageState();
}

class _WalletPageState extends State<WalletPage> {
  late Future<List<Map<String, dynamic>>> future;
  @override
  void initState() {
    super.initState();
    future = _load();
  }

  Future<List<Map<String, dynamic>>> _load() async {
    final api = ApiClient();
    final wallet = await api.get('/api/wallet');
    final transactions = await api.get('/api/wallet/transactions');
    Map<String, dynamic> config;
    try {
      config = await api.get('/api/app-config');
    } catch (_) {
      config = {
        'success': true,
        'data': {'wallet_topup_deep_link': defaultWalletTopUpLink}
      };
    }
    return [wallet, transactions, config];
  }

  Future<void> _topUp(String link) async {
    if (link.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Wallet top-up is not configured yet.')));
      return;
    }
    final uri = Uri.tryParse(link.trim());
    if (uri == null ||
        !await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('No payment app could open this link.')));
      }
    }
  }

  @override
  Widget build(BuildContext c) => SafeArea(
      child: FutureBuilder<List<Map<String, dynamic>>>(
          future: future,
          builder: (_, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            final wallet =
                snapshot.data?[0]['data'] as Map<String, dynamic>? ?? {};
            final transactions = snapshot.data?[1]['data'] as List? ?? [];
            final config =
                snapshot.data?[2]['data'] as Map<String, dynamic>? ?? {};
            final balance =
                (wallet['available_balance'] as num?)?.toStringAsFixed(0) ??
                    '0';
            return RefreshIndicator(
                onRefresh: () async => setState(() => future = _load()),
                child: ListView(padding: const EdgeInsets.all(20), children: [
                  const Text('Wallet',
                      style:
                          TextStyle(fontSize: 29, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 25),
                  Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(26),
                      decoration: BoxDecoration(
                          gradient: const LinearGradient(
                              colors: [Color(0xFF5D3DB7), Color(0xFF29204E)]),
                          borderRadius: BorderRadius.circular(24)),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('AVAILABLE CREDIT',
                                style: TextStyle(
                                    color: Colors.white60,
                                    letterSpacing: 1.5,
                                    fontSize: 11)),
                            const SizedBox(height: 8),
                            Text('₹$balance',
                                style: const TextStyle(
                                    fontSize: 42, fontWeight: FontWeight.w900)),
                            const SizedBox(height: 20),
                            SizedBox(
                                width: double.infinity,
                                child: FilledButton.icon(
                                    onPressed: () => _topUp(
                                        config['wallet_topup_deep_link'] ??
                                            defaultWalletTopUpLink),
                                    style: FilledButton.styleFrom(
                                        backgroundColor: gold,
                                        foregroundColor: ink),
                                    icon: const Icon(Icons.add_card_rounded),
                                    label: const Text('Top up wallet',
                                        style: TextStyle(
                                            fontWeight: FontWeight.w900)))),
                            const SizedBox(height: 16),
                            const Text(
                                'Referral credits can only be used under applicable lottery rules.',
                                style: TextStyle(color: Colors.white60))
                          ])),
                  const SizedBox(height: 26),
                  const Text('Transactions',
                      style:
                          TextStyle(fontWeight: FontWeight.w800, fontSize: 19)),
                  const SizedBox(height: 12),
                  if (transactions.isEmpty)
                    const Padding(
                        padding: EdgeInsets.only(top: 90),
                        child: Center(
                            child: Text('No transactions yet',
                                style: TextStyle(color: Colors.white38))))
                  else
                    ...transactions.map((x) => ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: CircleAvatar(
                            backgroundColor: gold.withValues(alpha: .12),
                            child: Icon(
                                (x['amount'] as num) >= 0
                                    ? Icons.south_west_rounded
                                    : Icons.north_east_rounded,
                                color: gold)),
                        title: Text(x['description'] ??
                            x['type'] ??
                            'Wallet transaction'),
                        subtitle: Text(
                            x['created_at']?.toString().split('T').first ?? ''),
                        trailing: Text('₹${x['amount']}',
                            style:
                                const TextStyle(fontWeight: FontWeight.w800))))
                ]));
          }));
}

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});
  @override
  Widget build(BuildContext c) => SafeArea(
      child: Padding(
          padding: const EdgeInsets.all(20),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Profile',
                style: TextStyle(fontSize: 29, fontWeight: FontWeight.w900)),
            const SizedBox(height: 28),
            const Center(
                child: CircleAvatar(
                    radius: 43,
                    backgroundColor: Color(0xFF272238),
                    child: Icon(Icons.person, size: 42, color: gold))),
            const SizedBox(height: 20),
            for (final x in [
              ('Personal details', Icons.person_outline, 'personal'),
              ('UPI & payment', Icons.account_balance_outlined, 'upi'),
              ('Delivery address', Icons.local_shipping_outlined, 'address'),
              ('Invite friends', Icons.group_add_outlined, 'invite'),
              ('Terms & privacy', Icons.shield_outlined, 'legal')
            ])
              ListTile(
                  onTap: () => Navigator.push(
                      c,
                      MaterialPageRoute(
                          builder: (_) => x.$3 == 'invite'
                              ? const InviteFriendsPage()
                              : x.$3 == 'legal'
                                  ? const TermsPrivacyPage()
                                  : ProfileEditPage(section: x.$3))),
                  leading: Icon(x.$2, color: Colors.white60),
                  title: Text(x.$1),
                  trailing:
                      const Icon(Icons.chevron_right, color: Colors.white24)),
            ListTile(
                onTap: () async {
                  await const FlutterSecureStorage().deleteAll();
                  if (c.mounted) {
                    Navigator.pushAndRemoveUntil(
                        c,
                        MaterialPageRoute(builder: (_) => const AuthPage()),
                        (_) => false);
                  }
                },
                leading: const Icon(Icons.logout, color: Colors.redAccent),
                title: const Text('Logout',
                    style: TextStyle(color: Colors.redAccent)))
          ])));
}

class ProfileEditPage extends StatefulWidget {
  const ProfileEditPage({super.key, required this.section});
  final String section;
  @override
  State<ProfileEditPage> createState() => _ProfileEditPageState();
}

class _ProfileEditPageState extends State<ProfileEditPage> {
  final fields = <String, TextEditingController>{};
  bool loading = true, saving = false;
  String? error;
  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in fields.values) {
      c.dispose();
    }
    super.dispose();
  }

  List<(String, String, IconData)> get specs => widget.section == 'personal'
      ? [
          ('full_name', 'Full name', Icons.person_outline),
          ('mobile', 'Mobile number', Icons.phone_outlined)
        ]
      : widget.section == 'upi'
          ? [('upi_id', 'Your UPI ID', Icons.account_balance_outlined)]
          : [
              ('address', 'Address', Icons.home_outlined),
              ('city', 'City', Icons.location_city_outlined),
              ('state', 'State', Icons.map_outlined),
              ('pincode', 'PIN code', Icons.pin_drop_outlined)
            ];
  String get title => widget.section == 'personal'
      ? 'Personal details'
      : widget.section == 'upi'
          ? 'UPI & payment'
          : 'Delivery address';

  Future<void> _load() async {
    try {
      final data = (await ApiClient().get('/api/users/me'))['data'];
      for (final spec in specs) {
        fields[spec.$1] = TextEditingController(text: '${data[spec.$1] ?? ''}');
      }
    } catch (e) {
      error = e.toString().replaceFirst('Exception: ', '');
    }
    if (mounted) setState(() => loading = false);
  }

  Future<void> _save() async {
    setState(() {
      saving = true;
      error = null;
    });
    try {
      final body = <String, dynamic>{};
      for (final spec in specs) {
        if (spec.$1 != 'mobile') body[spec.$1] = fields[spec.$1]!.text.trim();
      }
      await ApiClient().put('/api/users/me', body);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Details saved successfully.')));
      }
    } catch (e) {
      if (mounted) {
        setState(() => error = e.toString().replaceFirst('Exception: ', ''));
      }
    }
    if (mounted) setState(() => saving = false);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: Text(title)),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(padding: const EdgeInsets.all(20), children: [
              for (final spec in specs)
                Padding(
                    padding: const EdgeInsets.only(bottom: 14),
                    child: TextField(
                        controller: fields[spec.$1],
                        readOnly: spec.$1 == 'mobile',
                        keyboardType:
                            spec.$1 == 'pincode' ? TextInputType.number : null,
                        decoration: InputDecoration(
                            labelText: spec.$2,
                            prefixIcon: Icon(spec.$3),
                            helperText: spec.$1 == 'mobile'
                                ? 'Mobile number cannot be changed here'
                                : null))),
              if (error != null)
                Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Text(error!,
                        style: const TextStyle(color: Colors.redAccent))),
              FilledButton(
                  onPressed: saving ? null : _save,
                  style: FilledButton.styleFrom(
                      backgroundColor: gold, foregroundColor: ink),
                  child: Text(saving ? 'Saving…' : 'Save changes',
                      style: const TextStyle(fontWeight: FontWeight.w900)))
            ]));
}

class InviteFriendsPage extends StatelessWidget {
  const InviteFriendsPage({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Invite friends')),
      body: FutureBuilder<Map<String, dynamic>>(
          future: ApiClient().get('/api/referrals'),
          builder: (_, s) {
            if (s.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            final data = s.data?['data'] as Map<String, dynamic>? ?? {};
            final code = '${data['code'] ?? ''}';
            return Padding(
                padding: const EdgeInsets.all(20),
                child: Column(children: [
                  const Icon(Icons.group_add_rounded, size: 72, color: gold),
                  const SizedBox(height: 20),
                  const Text('Invite friends, earn rewards',
                      style:
                          TextStyle(fontSize: 23, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  const Text('Share your unique referral code.',
                      style: TextStyle(color: Colors.white54)),
                  const SizedBox(height: 26),
                  Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: .05),
                          borderRadius: BorderRadius.circular(18)),
                      child: Column(children: [
                        const Text('YOUR CODE',
                            style: TextStyle(
                                color: Colors.white54, letterSpacing: 1.5)),
                        const SizedBox(height: 8),
                        Text(code,
                            style: const TextStyle(
                                fontSize: 28,
                                color: gold,
                                fontWeight: FontWeight.w900))
                      ])),
                  const SizedBox(height: 18),
                  SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                          onPressed: () async {
                            await Clipboard.setData(ClipboardData(text: code));
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(
                                      content: Text('Referral code copied.')));
                            }
                          },
                          icon: const Icon(Icons.copy_rounded),
                          label: const Text('Copy referral code'))),
                  const SizedBox(height: 22),
                  Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _ReferralStat('${data['total'] ?? 0}', 'Invited'),
                        _ReferralStat(
                            '${data['successful'] ?? 0}', 'Successful')
                      ])
                ]));
          }));
}

class _ReferralStat extends StatelessWidget {
  const _ReferralStat(this.value, this.label);
  final String value, label;
  @override
  Widget build(BuildContext context) => Column(children: [
        Text(value,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
        Text(label, style: const TextStyle(color: Colors.white54))
      ]);
}

class TermsPrivacyPage extends StatelessWidget {
  const TermsPrivacyPage({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Terms & privacy')),
      body: FutureBuilder<Map<String, dynamic>>(
          future: ApiClient().get('/api/app-config'),
          builder: (_, s) {
            if (s.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            final d = s.data?['data'] as Map<String, dynamic>? ?? {};
            return ListView(padding: const EdgeInsets.all(20), children: [
              _LegalBlock('Terms of use',
                  '${d['terms_text'] ?? 'Terms have not been published yet.'}'),
              _LegalBlock('Privacy policy',
                  '${d['privacy_text'] ?? 'Privacy policy has not been published yet.'}'),
              _LegalBlock('Support',
                  '${d['support_contact'] ?? 'Contact details have not been published yet.'}')
            ]);
          }));
}

class _LegalBlock extends StatelessWidget {
  const _LegalBlock(this.title, this.text);
  final String title, text;
  @override
  Widget build(BuildContext context) => Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: .05),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.white10)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
        const SizedBox(height: 10),
        Text(text, style: const TextStyle(color: Colors.white70, height: 1.5))
      ]));
}

class WinnersPage extends StatefulWidget {
  const WinnersPage({super.key});
  @override
  State<WinnersPage> createState() => _WinnersPageState();
}

class _WinnersPageState extends State<WinnersPage> {
  late Future<Map<String, dynamic>> result;
  @override
  void initState() {
    super.initState();
    result = ApiClient().get('/api/winners');
  }

  @override
  Widget build(BuildContext context) => SafeArea(
      child: Padding(
          padding: const EdgeInsets.all(20),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Verified Winners',
                style: TextStyle(fontSize: 29, fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            const Text('Every result is generated from an auditable draw.',
                style: TextStyle(color: Colors.white54)),
            const SizedBox(height: 22),
            Expanded(
                child: FutureBuilder<Map<String, dynamic>>(
                    future: result,
                    builder: (_, snapshot) {
                      if (snapshot.connectionState != ConnectionState.done) {
                        return const Center(child: CircularProgressIndicator());
                      }
                      final rows = (snapshot.data?['data'] as List?) ?? [];
                      if (rows.isEmpty) {
                        return const EmptyPage(
                            icon: Icons.emoji_events_outlined,
                            title: 'No results yet',
                            text:
                                'Completed draw winners will appear here automatically.');
                      }
                      return RefreshIndicator(
                          onRefresh: () async => setState(
                              () => result = ApiClient().get('/api/winners')),
                          child: ListView.builder(
                              itemCount: rows.length,
                              itemBuilder: (_, i) {
                                final x = rows[i];
                                final colors = [
                                  gold,
                                  const Color(0xFFC4C9D4),
                                  const Color(0xFFCB8660)
                                ];
                                return Container(
                                    margin: const EdgeInsets.only(bottom: 14),
                                    padding: const EdgeInsets.all(20),
                                    decoration: BoxDecoration(
                                        color:
                                            Colors.white.withValues(alpha: .05),
                                        border: Border.all(
                                            color: colors[
                                                    (x['position'] as int) - 1]
                                                .withValues(alpha: .35)),
                                        borderRadius:
                                            BorderRadius.circular(20)),
                                    child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                              [
                                                'FIRST PRIZE',
                                                'SECOND PRIZE',
                                                'THIRD PRIZE'
                                              ][(x['position'] as int) - 1],
                                              style: TextStyle(
                                                  color: colors[
                                                      (x['position'] as int) -
                                                          1],
                                                  fontWeight: FontWeight.w900,
                                                  letterSpacing: 1)),
                                          const SizedBox(height: 12),
                                          Text(x['lottery'],
                                              style: const TextStyle(
                                                  fontSize: 19,
                                                  fontWeight: FontWeight.w800)),
                                          const SizedBox(height: 8),
                                          Text(
                                              '${x['winner']} • ${x['ticket_number']}',
                                              style: const TextStyle(
                                                  color: Colors.white70)),
                                          Text(x['prize'],
                                              style:
                                                  const TextStyle(color: gold))
                                        ]));
                              }));
                    }))
          ])));
}

class EmptyPage extends StatelessWidget {
  const EmptyPage(
      {super.key, required this.icon, required this.title, required this.text});
  final IconData icon;
  final String title, text;
  @override
  Widget build(BuildContext c) => SafeArea(
      child: Center(
          child: Padding(
              padding: const EdgeInsets.all(30),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(icon, size: 62, color: gold),
                const SizedBox(height: 18),
                Text(title,
                    style: const TextStyle(
                        fontSize: 25, fontWeight: FontWeight.w900)),
                const SizedBox(height: 9),
                Text(text,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white54))
              ]))));
}
