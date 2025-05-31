from datetime import datetime, timedelta
import json
from trainer.models import TrainerCource, TrainerType,CourseSession
from .zego_service import ZegoCloudService  # Make sure this import is correct


class TrainerCourseService:

    @staticmethod
    def create_course(trainer, base_info, course_variant, thumbnail=None):
        if isinstance(base_info, str):
            base_info = json.loads(base_info)

        if isinstance(course_variant, str):
            course_variant = json.loads(course_variant)
      
        start_date = base_info.get('start_date')
        end_date = base_info.get('end_date')
        title = base_info.get('title')  

        if not start_date or not end_date or not title:
            raise ValueError("Fields 'title', 'start_date', and 'end_date' are required.")

        trainer_type_instance = TrainerType.objects.get(id=base_info['trainer_type'])
        
        # Create the course
        course = TrainerCource.objects.create(
            trainer=trainer,
            trainer_type=trainer_type_instance,
            description=base_info.get('description', ''),
            price=base_info['price'],
            max_participants=base_info['max_participants'],
            title=title,  
            start_time=course_variant['start_time'],
            end_time=course_variant['end_time'],
            days_of_week=course_variant['days_of_week'],
            start_date=start_date,
            end_date=end_date,
            status='pending',  # Sessions will be created when status changes to 'approved'
            thumbnail=thumbnail,
        )
        return course

    @staticmethod
    def approve_course(course_id):
        """Call this when course is approved to create sessions"""
        course = TrainerCource.objects.get(id=course_id)
        course.status = 'approved'
        course.save()
        
        # Create sessions for the approved course
        TrainerCourseService._create_sessions_for_course(course)
        return course

    @staticmethod
    def _create_sessions_for_course(course):
        """Internal method to create sessions for a course"""
        # Delete any existing future sessions if course was updated
        CourseSession.objects.filter(
            course=course,
            session_date__gte=datetime.now().date(),
            is_completed=False
        ).delete()
        
        # Generate sessions between start_date and end_date for specified days
        current_date = course.start_date
        while current_date <= course.end_date:
            if current_date.strftime('%a') in course.days_of_week:
                room_id = f"course_{course.id}_session_{current_date.strftime('%Y%m%d')}"
                ZegoCloudService.create_room(room_id, f"{course.title} - {current_date}")
                
                CourseSession.objects.create(
                    course=course,
                    session_date=current_date,
                    zego_room_id=room_id,
                    zego_token=""  
                )
            current_date += timedelta(days=1)