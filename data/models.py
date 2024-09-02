from django.db import models

class HeroData(models.Model):
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=250)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Hero Data"
        verbose_name_plural = "Hero Data"

class LoginPageData(models.Model):
    description = models.TextField()

    def __str__(self):
        return "Login"

    class Meta:
        verbose_name = "Login"
        verbose_name_plural = "Login Data"

class TicketData(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Ticket Data"
        verbose_name_plural = "Ticket Data"

class VideoSectionData(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    thumbnail = models.ImageField(blank=True, null=True, upload_to='video_thumbnails/')
    link = models.URLField(max_length=200)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Video Section Data"
        verbose_name_plural = "Video Section Data"

class OnBoardingToTheWalletData(models.Model):
    description = models.TextField()

    def __str__(self):
        return "Onboarding Data"

    class Meta:
        verbose_name = "Onboarding to the Wallet Data"
        verbose_name_plural = "Onboarding to the Wallet Data"

class ImageOnboarding(models.Model):
    onboarding_data = models.ForeignKey(OnBoardingToTheWalletData, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images_onboarding/')

    def __str__(self):
        return f"Image for {self.onboarding_data}"

    class Meta:
        verbose_name = "Image Onboarding"
        verbose_name_plural = "Image Onboardings"

class AboutTheTicketData(models.Model):
    description_1 = models.TextField()
    description_2 = models.TextField()

    def __str__(self):
        return "About the Ticket"

    class Meta:
        verbose_name = "About the Ticket Data"
        verbose_name_plural = "About the Ticket Data"

class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
