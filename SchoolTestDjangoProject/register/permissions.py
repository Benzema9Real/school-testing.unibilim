from rest_framework.permissions import BasePermission


class IsStudentPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.role == 'student'


class IsSchool_AdminPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.role == 'school_admin'


class IsSuper_AdminPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.role == 'super_admin'
