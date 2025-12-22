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

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        appBar: AppBar(title: const Text('Lights App')),

        // 👇 THIS IS THE IMPORTANT PART
        body: SafeArea(
          child: Column(
            children: [
              Expanded(
                child: SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                    ),
                    onPressed: () => sendButton('red'),
                    child: const Text(
                      'FAIL',
                      style: TextStyle(
                        fontSize: 48,
                        fontWeight: FontWeight.bold,
                      ),
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
                    onPressed: () => sendButton('white'),
                    child: const Text(
                      'PASS',
                      style: TextStyle(
                        fontSize: 48,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

Future<void> sendButton(String color) async {
  final uri = Uri.parse('https://lightsapp.turbovci.co.uk:12345/button');

  final client = HttpClient()
    ..badCertificateCallback =
        (X509Certificate cert, String host, int port) => true;

  try {
    final request = await client.postUrl(uri);

    request.headers.set(HttpHeaders.contentTypeHeader, 'application/json');
    request.headers.set(HttpHeaders.acceptHeader, 'application/json');

    final payload = {
      'button': color,
      'timestamp': DateTime.now().toIso8601String(),
    };

    request.add(utf8.encode(jsonEncode(payload)));

    final response = await request.close();
    final responseBody =
        await response.transform(utf8.decoder).join();

    print('Sent $color → ${response.statusCode}');
    print('Response body: $responseBody');

    client.close();
  } catch (e) {
    print('Error sending $color: $e');
  }
}
