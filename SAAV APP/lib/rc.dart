import 'package:flutter/material.dart';
import 'package:flutter_mjpeg/flutter_mjpeg.dart';
import 'package:joystick/joystick.dart';

import 'navigation.dart';

class Rc extends StatefulWidget {
  const Rc({super.key});

  @override
  _RcState createState() => _RcState();
}

class _RcState extends State<Rc> {
  final TextEditingController postController = TextEditingController();
  @override
  Widget build(BuildContext context) {
    bool isRunning = true;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Remote Control'),
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.arrow_circle_up),
            tooltip: 'go to navigation page',
            onPressed: () {
              Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const Navigation(),
                  ));
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          Column(
            children: <Widget>[
              // TextField(
              //   controller: postController,
              //   decoration: const InputDecoration(
              //     border: OutlineInputBorder(),
              //     hintText: 'enter a post URL',
              //   ),
              // ),
              // MaterialButton(
              //   color: Colors.black,
              //   onPressed: () async {
              //     final String postt = postController.text;
              //   },
              //   child: const Text(
              //     'post',
              //     style: TextStyle(
              //       color: Colors.white,
              //       fontStyle: FontStyle.italic,
              //       fontWeight: FontWeight.bold,
              //       fontSize: 22,
              //     ),
              //   ),
              // ),
              Expanded(
                child: Center(
                  child: Mjpeg(
                    isLive: isRunning,
                    stream:
                        "http://192.168.43.169:8000/", //'http://192.168.1.37:8081',
                  ),
                ),
              ),
            ],
          ),
          Joystick(
            size: 200,
            backgroundColor: Colors.grey[350],
            joystickMode: JoystickModes.all,
            isDraggable: true,
          ),
        ],
      ),
    );
  }
}
