from django import forms
from .models import StudentAccount

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentAccount
        fields = ['first_name', 'last_name', 'email', 'course', 'year_level', 'contact_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'course': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Select your course'),
                # Engineering & Architecture Courses
                ('BS Architecture', 'BS Architecture'),
                ('BS Chemical Engineering', 'BS Chemical Engineering'),
                ('BS Civil Engineering', 'BS Civil Engineering'),
                ('BS Computer Engineering', 'BS Computer Engineering'),
                ('BS Electrical Engineering', 'BS Electrical Engineering'),
                ('BS Electronics Engineering', 'BS Electronics Engineering'),
                ('BS Industrial Engineering', 'BS Industrial Engineering'),
                ('BS Mechanical Engineering', 'BS Mechanical Engineering'),
                ('BS Mechanical Engineering with Computational Science', 'BS Mechanical Engineering with Computational Science'),
                ('BS Mechanical Engineering with Mechatronics', 'BS Mechanical Engineering with Mechatronics'),
                ('BS Mining Engineering', 'BS Mining Engineering'),
                # Business & Accountancy Courses
                ('BS Accountancy', 'BS Accountancy'),
                ('BS Accounting Information Systems', 'BS Accounting Information Systems'),
                ('BS Management Accounting', 'BS Management Accounting'),
                ('BS Business Administration - Banking & Financial Management', 'BS Business Administration - Banking & Financial Management'),
                ('BS Business Administration - Business Analytics', 'BS Business Administration - Business Analytics'),
                ('BS Business Administration - General Business Management', 'BS Business Administration - General Business Management'),
                ('BS Business Administration - Human Resource Management', 'BS Business Administration - Human Resource Management'),
                ('BS Business Administration - Marketing Management', 'BS Business Administration - Marketing Management'),
                ('BS Business Administration - Operations Management', 'BS Business Administration - Operations Management'),
                ('BS Business Administration - Quality Management', 'BS Business Administration - Quality Management'),
                ('BS Hospitality Management', 'BS Hospitality Management'),
                ('BS Tourism Management', 'BS Tourism Management'),
                ('BS Office Administration', 'BS Office Administration'),
                ('Associate in Office Administration', 'Associate in Office Administration'),
                ('Bachelor in Public Administration', 'Bachelor in Public Administration'),
                # Arts, Sciences & Education Courses
                ('AB Communication', 'AB Communication'),
                ('AB English with Applied Linguistics', 'AB English with Applied Linguistics'),
                ('Bachelor of Elementary Education', 'Bachelor of Elementary Education'),
                ('Bachelor of Secondary Education - Major in English', 'Bachelor of Secondary Education - Major in English'),
                ('Bachelor of Secondary Education - Major in Filipino', 'Bachelor of Secondary Education - Major in Filipino'),
                ('Bachelor of Secondary Education - Major in Mathematics', 'Bachelor of Secondary Education - Major in Mathematics'),
                ('Bachelor of Secondary Education - Major in Science', 'Bachelor of Secondary Education - Major in Science'),
                ('Bachelor of Multimedia Arts', 'Bachelor of Multimedia Arts'),
                ('BS Biology', 'BS Biology'),
                ('BS Math with Applied Industrial Mathematics', 'BS Math with Applied Industrial Mathematics'),
                ('BS Psychology', 'BS Psychology'),
                # Nursing & Allied Health Sciences Courses
                ('BS Nursing', 'BS Nursing'),
                ('BS Pharmacy', 'BS Pharmacy'),
                ('BS Medical Technology', 'BS Medical Technology'),
                # Computer Studies Courses
                ('BS Information Technology', 'BS Information Technology'),
                ('BS Computer Science', 'BS Computer Science'),
                ('BS Information Systems', 'BS Information Systems'),
                # Criminal Justice
                ('BS Criminology', 'BS Criminology'),
            ]),
            'year_level': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Select your year level'),
                (1, '1st Year'),
                (2, '2nd Year'),
                (3, '3rd Year'),
                (4, '4th Year'),
                (5, '5th Year'),
            ]),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Number'}),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'course': 'Course/Degree',
            'year_level': 'Year Level',
            'contact_number': 'Contact Number',
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Auto-determine program based on course
        instance.program = self.get_program_from_course(instance.course)
        if commit:
            instance.save()
        return instance

    @staticmethod
    def get_program_from_course(course):
        """Automatically determine the college/program based on the course"""
        engineering_courses = [
            'BS Architecture', 'BS Chemical Engineering', 'BS Civil Engineering',
            'BS Computer Engineering', 'BS Electrical Engineering', 'BS Electronics Engineering',
            'BS Industrial Engineering', 'BS Mechanical Engineering',
            'BS Mechanical Engineering with Computational Science',
            'BS Mechanical Engineering with Mechatronics', 'BS Mining Engineering'
        ]
        
        business_courses = [
            'BS Accountancy', 'BS Accounting Information Systems', 'BS Management Accounting',
            'BS Business Administration - Banking & Financial Management',
            'BS Business Administration - Business Analytics',
            'BS Business Administration - General Business Management',
            'BS Business Administration - Human Resource Management',
            'BS Business Administration - Marketing Management',
            'BS Business Administration - Operations Management',
            'BS Business Administration - Quality Management',
            'BS Hospitality Management', 'BS Tourism Management', 'BS Office Administration',
            'Associate in Office Administration', 'Bachelor in Public Administration'
        ]
        
        arts_education_courses = [
            'AB Communication', 'AB English with Applied Linguistics',
            'Bachelor of Elementary Education', 'Bachelor of Secondary Education - Major in English',
            'Bachelor of Secondary Education - Major in Filipino',
            'Bachelor of Secondary Education - Major in Mathematics',
            'Bachelor of Secondary Education - Major in Science',
            'Bachelor of Multimedia Arts', 'BS Biology',
            'BS Math with Applied Industrial Mathematics', 'BS Psychology'
        ]
        
        nursing_courses = ['BS Nursing', 'BS Pharmacy', 'BS Medical Technology']
        
        computer_courses = ['BS Information Technology', 'BS Computer Science', 'BS Information Systems']
        
        criminal_justice_courses = ['BS Criminology']
        
        if course in engineering_courses:
            return 'College of Engineering and Architecture'
        elif course in business_courses:
            return 'College of Management, Business & Accountancy'
        elif course in arts_education_courses:
            return 'College of Arts, Sciences & Education'
        elif course in nursing_courses:
            return 'College of Nursing & Allied Health Sciences'
        elif course in computer_courses:
            return 'College of Computer Studies'
        elif course in criminal_justice_courses:
            return 'College of Criminal Justice'
        else:
            return 'Other'