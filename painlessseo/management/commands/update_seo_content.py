"""
sync_seo_models.py

    Goes through all the registered models syncing the seo information.

"""
from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError
from django.core.urlresolvers import resolve, Resolver404
from django.contrib.contenttypes.models import ContentType

from painlessseo import settings
from painlessseo.utils import (
    delete_seo, update_seo, get_fallback_metadata
    )
from painlessseo.models import SeoRegisteredModel, SeoMetadata
import hashlib

DEFAULT_CREATE_LANG = []
DEFAULT_SEO_MODELS = settings.SEO_MODELS


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--langs', dest='update_langs', default=DEFAULT_CREATE_LANG,
                    help='Use this to indicate which languages must be generated'),
        make_option('--models', dest='seo_models', default=DEFAULT_SEO_MODELS,
                    help='Use this to indicate which apps must be updated'),
    )
    help = '''DEBUG only: Sync the SEO info in the database for registered models. '''
    requires_model_validation = True

    def handle_noargs(self, **options):
        seo_models = options.get('seo_models')
        if isinstance(seo_models, str):
            models = seo_models.split(' ')
            seo_models = []
            for model in models:
                seo_models.append(model.split('.'))

        update_langs = options.get('update_langs')
        if isinstance(update_langs, str):
            langs = update_langs.split(' ')
            update_langs = []
            for lang in langs:
                update_langs.append(lang)
        languages = settings.SEO_LANGUAGES
        base_lang = settings.DEFAULT_LANG_CODE

        # Update SeoPath
        metadatas = SeoMetadata.objects.filter(
            lang_code=base_lang, content_type__isnull=True)

        count = 0
        for metadata in list(metadatas):
            # Each metadata, sync it for the rest of the languages
            view_name = metadata.view_name
            if view_name:
                for lang_code, language in languages:
                    # If not exists a metadata on this lang for this view
                    if not SeoMetadata.objects.filter(
                            lang_code=lang_code, view_name=view_name).exists():
                        SeoMetadata.objects.create(
                            lang_code=lang_code, view_name=view_name,
                            description=metadata.description,
                            title=metadata.title,
                            has_parameters=metadata.has_parameters,
                            path=metadata.path,
                            )
                        count += 1

        print(str(count) + " metadatas created.")

        # Update SeoModels
        count = 0
        for app, model in seo_models:
            ctype = ContentType.objects.get(app_label=app.lower(), model=model.lower())
            seomodels = SeoRegisteredModel.objects.filter(
                lang_code=base_lang, content_type=ctype)
            if seomodels.exists():
                for seomodel in seomodels:
                    for lang_code, language in languages:
                        # If not exists a metadata on this lang for this model
                        if not SeoRegisteredModel.objects.filter(
                                lang_code=lang_code, content_type=ctype).exists():
                            SeoRegisteredModel.objects.create(
                                lang_code=lang_code, content_type=ctype,
                                title=seomodel.title,
                                description=seomodel.description)
                            count += 1

        print(str(count) + " seomodels created.")
