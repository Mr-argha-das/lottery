import 'package:dhanlaxmi_lottery/main.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('constructs app and configured samples', () {
    expect(const DhanLaxmiApp(), isA<DhanLaxmiApp>());
    expect(samples.length, 2);
    expect(samples.first.price, 100);
  });
}
