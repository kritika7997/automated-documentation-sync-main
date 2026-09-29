from .service import ReviewService, ReviewView


def get_review_view(service: ReviewService, change_set, proposal, artifact) -> ReviewView:
    return service.present(change_set, proposal, artifact)


__all__ = ["get_review_view"]