from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Dataset, Student
from .utils import clean_and_parse_excel
from django.utils import timezone
import pandas as pd

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role', 'student') # 'student' or 'admin'

        if role == 'admin':
            user = authenticate(username=username, password=password)
            if user and user.is_superuser:
                return Response({'token': 'admin-dummy-token', 'role': 'admin', 'username': user.username}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid Admin Credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        else: # Student Login
            # Check active dataset first
            active_dataset = Dataset.objects.filter(is_active=True).first()
            if not active_dataset:
                return Response({'error': 'No active exam info found. Pending for admin access.'}, status=status.HTTP_403_FORBIDDEN)
            
            try:
                # Filter by active dataset and credentials
                student = Student.objects.get(register_no=username, password=password, dataset=active_dataset)
                return Response({
                    'role': 'student',
                    'name': student.name,
                    'register_no': student.register_no,
                    'course_code': student.course_code,
                    'course_title': student.course_title,
                    'exam_date': student.exam_date,
                    'session': student.session,
                    'hall_no': student.hall_no,
                    'seat_no': student.seat_no
                }, status=status.HTTP_200_OK)
            except Student.DoesNotExist:
                return Response({'error': 'Invalid Credentials or Student not found in active list'}, status=status.HTTP_401_UNAUTHORIZED)


class DatasetUploadView(APIView):
    def post(self, request):
        # Only allow simpler validation for now (assume admin checks handled via token or session, but for quick prototype we skip strict auth check here or add simple one if needed)
        # For full security we'd check headers.
        
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = clean_and_parse_excel(file)
            
            # Create Dataset
            dataset = Dataset.objects.create(file=file, is_active=False)
            
            # Create Students
            students_to_create = []
            for _, row in df.iterrows():
                # Format Date if needed
                e_date = row.get('exam_date')
                parsed_date = None
                
                # Try to parse the exam_date
                if pd.notna(e_date):
                    try:
                        # Convert to datetime and then to date
                        parsed_date = pd.to_datetime(e_date).date()
                    except:
                        # If parsing fails, try to keep as string and let Django handle it
                        try:
                            parsed_date = str(e_date).split()[0] if e_date else None
                        except:
                            parsed_date = None
                
                students_to_create.append(Student(
                    dataset=dataset,
                    register_no=str(row.get('register_no', '')),
                    name=str(row.get('name', '')),
                    course_code=str(row.get('course_code', '')),
                    course_title=str(row.get('course_title', '')),
                    exam_date=parsed_date, 
                    session=str(row.get('session', '')),
                    hall_no=str(row.get('hall_no', '')),
                    seat_no=str(row.get('seat_no', ''))
                ))
            
            Student.objects.bulk_create(students_to_create)
            
            return Response({'message': 'Dataset uploaded successfully', 'students_count': len(students_to_create), 'dataset_id': dataset.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DatasetListView(APIView):
    def get(self, request):
        datasets = Dataset.objects.all().order_by('-uploaded_at')
        data = []
        for d in datasets:
            data.append({
                'id': d.id,
                'uploaded_at': d.uploaded_at,
                'is_active': d.is_active,
                'student_count': d.students.count()
            })
        return Response(data)

class ToggleDatasetView(APIView):
    def post(self, request, pk):
        try:
            dataset = Dataset.objects.get(pk=pk)
            # Deactivate all others if activating this one
            if not dataset.is_active:
                Dataset.objects.update(is_active=False)
                dataset.is_active = True
            else:
                dataset.is_active = False # Toggle off
            dataset.save()
            return Response({'message': f"Dataset {'activated' if dataset.is_active else 'deactivated'}", 'is_active': dataset.is_active})
        except Dataset.DoesNotExist:
            return Response({'error': 'Dataset not found'}, status=status.HTTP_404_NOT_FOUND)

class DeleteStudentsView(APIView):
    def delete(self, request):
        Dataset.objects.all().delete() # Cascades to students
        return Response({'message': 'All data cleared'})
