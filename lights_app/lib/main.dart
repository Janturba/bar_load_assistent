import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';

void main() {
  HttpOverrides.global = MyHttpOverrides();
  runApp(const MyApp());
}

class MyHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    final client = super.createHttpClient(context);
    client.badCertificateCallback =
        (X509Certificate cert, String host, int port) => true;
    return client;
  }
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  String? selectedReferee;
  String? errorMessage;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        body: SafeArea(
          child: selectedReferee == null
              ? buildRefereeSelection()
              : buildVotingScreen(),
        ),
      ),
    );
  }

  // =========================
  // SCREEN 1 — REFEREE PICK
  // =========================
  Widget buildRefereeSelection() {
    return Container(
      color: Colors.white,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          refereeButton("Left referee", "left"),
          refereeButton("Center referee", "center"),
          refereeButton("Right referee", "right"),
          if (errorMessage != null) ...[
            const SizedBox(height: 30),
            Text(
              errorMessage!,
              style: const TextStyle(
                color: Colors.red,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget refereeButton(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 40),
      child: SizedBox(
        width: double.infinity,
        height: 80,
        child: ElevatedButton(
          onPressed: () => registerReferee(value),
          child: Text(
            label,
            style: const TextStyle(fontSize: 22),
          ),
        ),
      ),
    );
  }

  // =========================
  // SCREEN 2 — VOTING
  // =========================
  Widget buildVotingScreen() {
    return Column(
      children: [
        Expanded(
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
              ),
              onPressed: () => sendVote("red"),
              child: const Text(
                "FAIL",
                style: TextStyle(fontSize: 48, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ),
        Expanded(
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: Colors.black,
              ),
              onPressed: () => sendVote("white"),
              child: const Text(
                "PASS",
                style: TextStyle(fontSize: 48, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // =========================
  // NETWORK CALLS
  // =========================
  Future<void> registerReferee(String referee) async {
    final uri = Uri.parse("https://lightsapp.turbovci.co.uk:12345/button");
    final client = HttpClient()
      ..badCertificateCallback =
          (X509Certificate cert, String host, int port) => true;

    final payload = {
      "action": "register",
      "referee": referee,
    };

    try {
      final request = await client.postUrl(uri);
      request.headers.set(HttpHeaders.contentTypeHeader, "application/json");
      request.add(utf8.encode(jsonEncode(payload)));

      final response = await request.close();
      final body = await response.transform(utf8.decoder).join();
      final data = jsonDecode(body);

      if (data["ok"] == true) {
        setState(() {
          selectedReferee = referee;
          errorMessage = null;
        });
      } else {
        setState(() {
          errorMessage = data["message"] ?? "Referee already taken";
        });
      }
    } catch (e) {
      setState(() {
        errorMessage = "Server error: $e";
      });
    } finally {
      client.close();
    }
  }

  Future<void> sendVote(String color) async {
    final uri = Uri.parse("https://lightsapp.turbovci.co.uk:12345/button");
    final client = HttpClient()
      ..badCertificateCallback =
          (X509Certificate cert, String host, int port) => true;

    final payload = {
      "action": "vote",
      "referee": selectedReferee,
      "button": color,
    };

    try {
      final request = await client.postUrl(uri);
      request.headers.set(HttpHeaders.contentTypeHeader, "application/json");
      request.add(utf8.encode(jsonEncode(payload)));
      await request.close();
    } catch (e) {
      print("Vote error: $e");
    } finally {
      client.close();
    }
  }
}
