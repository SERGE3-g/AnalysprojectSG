import json
import datetime
import matplotlib.pyplot as plt 
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

@dataclass
class TestTimes:
    start_time: str
    end_time: str
    elapsed_time: float

@dataclass 
class TestResult:
    name: str
    status: str
    message: str
    times: TestTimes
    tags: List[str]
    doc: str
    is_critical: bool

@dataclass
class SuiteResult:
    name: str
    doc: str
    status: str
    message: str
    start_time: str
    end_time: str
    elapsed_time: float
    tests: List[TestResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    metadata: Dict[str, str]

class TestAnalyzer:
    """Class for analyzing test results and generating statistics"""
    
    def __init__(self, suite_results: SuiteResult):
        self.suite_results = suite_results
        self.test_df = self._create_dataframe()
        
    def _create_dataframe(self) -> pd.DataFrame:
        """Convert test results to pandas DataFrame for analysis"""
        data = []
        for test in self.suite_results.tests:
            data.append({
                'name': test.name,
                'status': test.status,
                'duration': test.times.elapsed_time,
                'tags': ','.join(test.tags),
                'is_critical': test.is_critical
            })
        return pd.DataFrame(data)
    
    def get_slowest_tests(self, n: int = 5) -> pd.DataFrame:
        """Get the n slowest tests"""
        return self.test_df.nlargest(n, 'duration')
    
    def get_failure_rate_by_tag(self) -> pd.Series:
        """Calculate failure rate for each tag"""
        tag_results = {}
        for test in self.suite_results.tests:
            for tag in test.tags:
                if tag not in tag_results:
                    tag_results[tag] = {'total': 0, 'failed': 0}
                tag_results[tag]['total'] += 1
                if test.status == 'FAIL':
                    tag_results[tag]['failed'] += 1
                    
        failure_rates = {}
        for tag, counts in tag_results.items():
            failure_rates[tag] = (counts['failed'] / counts['total']) * 100
            
        return pd.Series(failure_rates)
    
    def plot_duration_histogram(self, output_file: str):
        """Create histogram of test durations"""
        plt.figure(figsize=(10, 6))
        plt.hist(self.test_df['duration'], bins=20)
        plt.title('Distribution of Test Durations')
        plt.xlabel('Duration (seconds)')
        plt.ylabel('Number of Tests')
        plt.savefig(output_file)
        plt.close()
        
    def plot_status_pie_chart(self, output_file: str):
        """Create pie chart of test statuses"""
        status_counts = self.test_df['status'].value_counts()
        plt.figure(figsize=(8, 8))
        plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%')
        plt.title('Test Results Distribution')
        plt.savefig(output_file)
        plt.close()

class TestReportGenerator:
    def __init__(self, report_file: str):
        self.report_file = report_file
        self.suite_results = None
        self.analyzer = None
        
    def parse_report(self):
        """Parse the test report file (XML or JSON)"""
        if self.report_file.endswith('.xml'):
            self._parse_xml()
        else:
            self._parse_json()
        
        if self.suite_results:
            self.analyzer = TestAnalyzer(self.suite_results)
            
    def _parse_xml(self):
        """Parse Robot Framework XML output file"""
        tree = ET.parse(self.report_file)
        root = tree.getroot()
        
        suite = root.find('suite')
        if suite is None:
            raise ValueError("No test suite found in report")
            
        self.suite_results = self._parse_suite(suite)
        
    def _parse_json(self):
        """Parse JSON report file"""
        with open(self.report_file) as f:
            data = json.load(f)
            
        # Implement JSON parsing based on your format
        pass
        
    def _parse_suite(self, suite_elem) -> SuiteResult:
        """Parse a suite element from XML"""
        tests = []
        for test_elem in suite_elem.findall('.//test'):
            test = self._parse_test(test_elem)
            tests.append(test)
            
        stats = suite_elem.find('statistics/total')
        total = int(stats.get('all', 0))
        passed = int(stats.get('pass', 0))
        
        return SuiteResult(
            name=suite_elem.get('name'),
            doc=suite_elem.findtext('doc', ''),
            status=suite_elem.find('status').get('status'),
            message=suite_elem.find('status').get('message', ''),
            start_time=suite_elem.get('starttime', ''),
            end_time=suite_elem.get('endtime', ''),
            elapsed_time=float(suite_elem.get('elapsedtime', 0)),
            tests=tests,
            total_tests=total,
            passed_tests=passed,
            failed_tests=total - passed,
            metadata=self._parse_metadata(suite_elem)
        )
    
    def generate_pdf_report(self, output_file: str):
        """Generate detailed PDF report"""
        if not self.suite_results:
            raise ValueError("No test results parsed yet")
            
        doc = SimpleDocTemplate(output_file, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        elements.append(Paragraph(f"Test Execution Report - {self.suite_results.name}", styles['Title']))
        
        # Summary
        elements.append(Paragraph("Summary", styles['Heading1']))
        summary_data = [
            ["Total Tests", str(self.suite_results.total_tests)],
            ["Passed Tests", str(self.suite_results.passed_tests)],
            ["Failed Tests", str(self.suite_results.failed_tests)],
            ["Duration", f"{self.suite_results.elapsed_time:.2f}s"]
        ]
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        
        # Test Results
        elements.append(Paragraph("Test Results", styles['Heading1']))
        test_data = [["Name", "Status", "Duration", "Tags"]]
        for test in self.suite_results.tests:
            test_data.append([
                test.name,
                test.status,
                f"{test.times.elapsed_time:.2f}s",
                ", ".join(test.tags)
            ])
        
        test_table = Table(test_data)
        test_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(test_table)
        
        doc.build(elements)

    def send_email_report(self, 
                         sender: str,
                         recipients: List[str],
                         smtp_server: str,
                         smtp_port: int,
                         username: str,
                         password: str,
                         attach_reports: bool = True):
        """Send email report with optional PDF and HTML attachments"""
        
        msg = MIMEMultipart()
        msg['Subject'] = f"Test Execution Report - {self.suite_results.name}"
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)
        
        # Create email body
        body = f"""
        Test Execution Summary:
        
        Suite: {self.suite_results.name}
        Total Tests: {self.suite_results.total_tests}
        Passed: {self.suite_results.passed_tests}
        Failed: {self.suite_results.failed_tests}
        Duration: {self.suite_results.elapsed_time:.2f}s
        
        Please see attached reports for details.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach reports if requested
        if attach_reports:
            # Generate and attach PDF report
            pdf_file = "temp_report.pdf"
            self.generate_pdf_report(pdf_file)
            with open(pdf_file, "rb") as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                pdf_attachment.add_header(
                    'Content-Disposition', 'attachment', filename="test_report.pdf")
                msg.attach(pdf_attachment)
            
            # Generate and attach HTML report
            html_file = "temp_report.html"
            self.generate_html_report(html_file)
            with open(html_file, "r") as f:
                html_attachment = MIMEText(f.read(), 'html')
                html_attachment.add_header(
                    'Content-Disposition', 'attachment', filename="test_report.html")
                msg.attach(html_attachment)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)

    def export_to_json(self, output_file: str):
        """Export test results to JSON format"""
        if not self.suite_results:
            raise ValueError("No test results parsed yet")
            
        def convert_to_dict(obj):
            if hasattr(obj, '__dict__'):
                return {key: convert_to_dict(value) 
                        for key, value in obj.__dict__.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_to_dict(value) 
                        for key, value in obj.items()}
            return obj
            
        with open(output_file, 'w') as f:
            json.dump(convert_to_dict(self.suite_results), f, indent=2)

def main():
    # Example usage
    report_generator = TestReportGenerator("output.xml")
    report_generator.parse_report()
    
    # Generate different types of reports
    report_generator.generate_html_report("test_report.html")
    report_generator.generate_pdf_report("test_report.pdf")
    report_generator.export_to_json("test_results.json")
    
    # Generate analytics
    report_generator.analyzer.plot_duration_histogram("duration_histogram.png")
    report_generator.analyzer.plot_status_pie_chart("status_pie.png")
    
    # Print slowest tests
    slowest_tests = report_generator.analyzer.get_slowest_tests()
    print("\nSlowest Tests:")
    print(slowest_tests)
    
    # Print failure rates by tag
    failure_rates = report_generator.analyzer.get_failure_rate_by_tag()
    print("\nFailure Rates by Tag:")
    print(failure_rates)
    
    # Send email report
    report_generator.send_email_report(
        sender="test@example.com",
        recipients=["team@example.com"],
        smtp_server="smtp.example.com",
        smtp_port=587,
        username="user",
        password="pass"
    )

if __name__ == "__main__":
    main()