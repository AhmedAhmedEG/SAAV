import 'dart:io';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const MyApp());
}

class SensorData {
  double x, y, z;
  SensorData(this.x, this.y, this.z);

  Map<String, dynamic> toJson() {
    return {"x": x, "y": y, "z": z};
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MediaQuery(
      data: MediaQueryData(),
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'My App',
        home: SensorScreen(),
      ),
    );
  }
}

class SensorScreen extends StatefulWidget {
  const SensorScreen({super.key});

  @override
  _SensorScreenState createState() => _SensorScreenState();
}

class _SensorScreenState extends State<SensorScreen> {
// This widget is the root of your application.

  String _gyroscopeData = '';
  String _accelerometerData = '';
  String _manualHeadingdata = '';

  double _gyroscopeX = 0.0;
  double _gyroscopeY = 0.0;
  double _gyroscopeZ = 0.0;

  double _accelerometerX = 0.0;
  double _accelerometerY = 0.0;
  double _accelerometerZ = 0.0;

  double _magnometerX = 0.0;
  double _magnometerY = 0.0;
  double _magnometerZ = 0.0;

  double _manualHeading = 0.0;

  @override
  void initState() {
    super.initState();
    setUpServer();
    setUpSensors();
    // setUpSensors();
  }

  void setUpServer() async {
    HttpServer.bind('0.0.0.0', 8080).then((HttpServer server) {
      server.listen(respond);
    });
    // Map<String, String> data = {
    //   'gyroscope': _gyroscopeData,
    //   'acceleometer': _accelerometerData,
    //   'heading': _manualHeadingdata,
    // };
  }

  void respond(HttpRequest request) {
    request.response.write(
      {
        "gyroX:$_gyroscopeX,gyroY:$_gyroscopeY,gyroZ:$_gyroscopeZ,AcceX:$_accelerometerX,AcceY:$_accelerometerY,AcceZ:$_accelerometerZ,heading:$_manualHeading"
      },
    );
    request.response.close();
  }

  void setUpSensors() {
    gyroscopeEvents.listen((GyroscopeEvent event) {
      setState(() {
        _gyroscopeX = event.x;
        _gyroscopeY = event.y;
        _gyroscopeZ = event.z;
        _gyroscopeData =
            'x: ${_gyroscopeX.toStringAsFixed(3)},y: ${_gyroscopeY.toStringAsFixed(3)}z: ${_gyroscopeZ.toStringAsFixed(3)},';
      });
    });

    accelerometerEvents.listen((AccelerometerEvent event) {
      setState(() {
        _accelerometerX = event.x;
        _accelerometerY = event.y;
        _accelerometerZ = event.z;
        _accelerometerData =
            'x: ${_accelerometerX.toStringAsFixed(3)}, y: ${_accelerometerY.toStringAsFixed(3)},z: ${_accelerometerZ.toStringAsFixed(3)}';
      });
    });

    magnetometerEvents.listen((MagnetometerEvent event) {
      setState(() {
        _magnometerX = event.x;
        _magnometerY = event.y;
        _magnometerZ = event.z;
        calculateManualHeading();
      });
    });
  }

  double calculateManualHeading() {
    // Calculate the magnetic north vector using the magnetometer readings and a rotation matrix
    final double mx = _magnometerX;
    final double my = _magnometerY;
    final double mz = _magnometerZ;
    final double m_norm = sqrt(mx * mx + my * my + mz * mz);
    final double mx_north = mx / m_norm;
    final double my_north = my / m_norm;
    final double mz_north = mz / m_norm;

    // Calculate the gravity vector using the accelerometer readings
    final double ax = _accelerometerX;
    final double ay = _accelerometerY;
    final double az = _accelerometerZ;
    final double a_norm = sqrt(ax * ax + ay * ay + az * az);
    final double ax_gravity = ax / a_norm;
    final double ay_gravity = ay / a_norm;
    final double az_gravity = az / a_norm;

    // Calculate the east vector by taking the cross product of the magnetic north vector and the gravity vector
    final double ex = ay_gravity * mz_north - az_gravity * my_north;
    final double ey = az_gravity * mx_north - ax_gravity * mz_north;
    final double ez = ax_gravity * my_north - ay_gravity * mx_north;
    final double e_norm = sqrt(ex * ex + ey * ey + ez * ez);
    final double ex_east = ex / e_norm;
    final double ey_east = ey / e_norm;
    final double ez_east = ez / e_norm;

    // Calculate the north vector by taking the cross product of the east vector and the magnetic north vector
    final double nx = ey_east * mz_north - ez_east * my_north;
    final double ny = ez_east * mx_north - ex_east * mz_north;
    final double nz = ex_east * my_north - ey_east * mx_north;
    final double n_norm = sqrt(nx * nx + ny * ny + nz * nz);
    final double nx_north = nx / n_norm;
    final double ny_north = ny / n_norm;
    final double nz_north = nz / n_norm;

    // Calculate theazimuth angle (i.e., the heading) using the east and north vectors and the y-axis of the device
    _manualHeading = atan2(ex_east * 0 + ey_east * 1 + ez_east * 0,
            nx_north * 0 + ny_north * 1 + nz_north * 0) *
        180 /
        pi;
    _manualHeadingdata = "heading: $_manualHeading";
    return _manualHeading.toStringAsFixed(3) as double;
  }

  // Future<void> sendSensorData() async {
  //   Map<String, String> data = {
  //     'gyroscope': _gyroscopeData,
  //     'acceleometer': _accelerometerData,
  //     'heading': _manualHeadingdata,
  //   };
  //   String url = "http://localhost:8080";
  //   try {
  //     await http.post(
  //       Uri.parse('$url/sensor'),
  //       body: jsonEncode(data),
  //     );
  //   } catch (e) {
  //     print('Error sending sensor data: $e');
  //   }
  // }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        backgroundColor: Colors.teal[200],
        appBar: AppBar(
          backgroundColor: Colors.teal[900],
          centerTitle: true,
          title: const Text(
            'Sensor Readings',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 30,
              fontStyle: FontStyle.italic,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const Text(
                'Gyroscope Readings:',
                style: TextStyle(
                    fontSize: 25,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic),
              ),
              Text(
                'X: $_gyroscopeX',
                style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic),
              ),
              Text(
                'Y: $_gyroscopeY',
                style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic),
              ),
              Text(
                'Z: $_gyroscopeZ',
                style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic),
              ),
              const SizedBox(
                height: 25,
              ),
              const Text(
                'Accelerometer Readings:',
                style: TextStyle(
                    fontSize: 25,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic),
              ),
              Text(
                'X: $_accelerometerX',
                style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic),
              ),
              Text(
                'Y: $_accelerometerY',
                style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic),
              ),
              Text(
                'Z: $_accelerometerZ',
                style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic),
              ),
              const SizedBox(
                height: 25,
              ),
              Text(
                'Heading: $_manualHeading',
                style: const TextStyle(
                    fontSize: 25,
                    fontWeight: FontWeight.bold,
                    fontStyle: FontStyle.italic),
              ),
              const SizedBox(
                height: 20,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
