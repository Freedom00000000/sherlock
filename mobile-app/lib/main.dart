import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  runApp(const SherlockApp());
}

class SherlockApp extends StatelessWidget {
  const SherlockApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sherlock',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF7C3AED),
          brightness: Brightness.dark,
          surface: const Color(0xFF1E1E2E),
        ),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF1E1E2E),
      ),
      home: const HomeScreen(),
    );
  }
}
