import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/main.dart';

void main() {
  testWidgets('Customer app renders welcome branding and login flow', (WidgetTester tester) async {
    await tester.pumpWidget(const LoanOrbitCustomerApp());
    await tester.pumpAndSettle();

    expect(find.text('LOANORBIT'), findsOneWidget);
    expect(find.text('Your Credit Journey, Clearly Guided.'), findsOneWidget);
    expect(find.text('Get Verification Code'), findsOneWidget);
  });
}
