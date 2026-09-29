from .service import ReviewService, ReviewView


def get_review_view(service: ReviewService, run_id: str, change_set, proposal, artifact) -> ReviewView:
    return service.present(run_id, change_set, proposal, artifact)


__all__ = ["get_review_view"]