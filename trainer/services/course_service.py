from trainer.models import TrainerCource
from trainer.models import TrainerType
import json


class TrainerCourseService:

    @staticmethod
    def create_course(trainer, base_info, course_variant):
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
            status='pending',
        )
        return course